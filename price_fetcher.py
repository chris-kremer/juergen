"""
Stock price fetching functionality with fallback to default values
"""

import copy
import threading
import time as time_module
import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Dict, List, Optional, Tuple
from translations import get_text


FX_TICKERS = {
    "USD": ("EURUSD=X", True),   # Yahoo quote is USD per EUR; invert it.
    "GBP": ("GBPEUR=X", False),  # Yahoo quote is EUR per GBP.
}


def _fetch_yfinance_history_uncached(symbol: str, period: str = None, start=None, end=None) -> pd.DataFrame:
    try:
        ticker = yf.Ticker(symbol)
        if period:
            return ticker.history(period=period)
        return ticker.history(start=start, end=end)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_yfinance_history(symbol: str, period: str = None, start=None, end=None) -> pd.DataFrame:
    """Cached Yahoo Finance history lookup shared across dashboard sections."""
    return _fetch_yfinance_history_uncached(symbol, period=period, start=start, end=end)


def _normalize_daily_index(index) -> pd.DatetimeIndex:
    normalized = pd.to_datetime(index)
    if normalized.tz is not None:
        normalized = normalized.tz_localize(None)
    return normalized.normalize()


def _fx_rates_for_index(currency: str, index, period: str = None, start=None, end=None):
    """Return quote-currency-to-EUR rates aligned to a security history."""
    if currency == "EUR":
        return pd.Series(1.0, index=index)

    fx_config = FX_TICKERS.get(currency)
    if fx_config is None:
        return None

    fx_symbol, invert = fx_config
    fx_history = fetch_yfinance_history(fx_symbol, period=period, start=start, end=end)
    if fx_history.empty or "Close" not in fx_history:
        return None

    fx_close = fx_history["Close"].astype(float).copy()
    fx_close.index = _normalize_daily_index(fx_close.index)
    target_dates = _normalize_daily_index(index)
    aligned = fx_close.reindex(target_dates, method="ffill").bfill()
    if aligned.isna().any() or (aligned == 0).any():
        return None
    if invert:
        aligned = 1.0 / aligned
    aligned.index = index
    return aligned


def convert_history_to_eur(stock: Dict, history: pd.DataFrame, period: str = None, start=None, end=None) -> pd.DataFrame:
    """Convert a Yahoo quote history to EUR per legal portfolio unit."""
    if history is None or history.empty:
        return pd.DataFrame()

    currency = stock.get("quote_currency", "EUR")
    quote_multiplier = float(stock.get("quote_multiplier", 1.0))
    fx_rates = _fx_rates_for_index(currency, history.index, period=period, start=start, end=end)
    if fx_rates is None:
        return pd.DataFrame()

    converted = history.copy()
    conversion = fx_rates * quote_multiplier
    for column in ("Open", "High", "Low", "Close"):
        if column in converted:
            converted[column] = converted[column].astype(float) * conversion
    converted.attrs["currency"] = "EUR"
    return converted


def fetch_stock_history_eur(stock: Dict, period: str = None, start=None, end=None, use_cache: bool = True) -> pd.DataFrame:
    """Fetch a security's price history and express every quote in EUR."""
    symbol = stock.get("symbol")
    if not symbol or symbol == "CASH":
        return pd.DataFrame()
    fetcher = fetch_yfinance_history if use_cache else _fetch_yfinance_history_uncached
    history = fetcher(symbol, period=period, start=start, end=end)
    return convert_history_to_eur(stock, history, period=period, start=start, end=end)


_PREFETCH_LOCK = threading.Lock()
_PREFETCH_RESULT: Optional[Tuple[List[Dict], List[str]]] = None
_PREFETCH_COMPLETED_AT = 0.0
_PREFETCH_IN_PROGRESS = False


def start_stock_price_prefetch(stocks: List[Dict], max_age_seconds: int = 300) -> str:
    """Start a background current-price download if no fresh result exists."""
    global _PREFETCH_IN_PROGRESS, _PREFETCH_RESULT, _PREFETCH_COMPLETED_AT

    now = time_module.time()
    with _PREFETCH_LOCK:
        if _PREFETCH_RESULT is not None and now - _PREFETCH_COMPLETED_AT <= max_age_seconds:
            return "ready"
        if _PREFETCH_IN_PROGRESS:
            return "running"
        _PREFETCH_IN_PROGRESS = True

    def _worker():
        global _PREFETCH_IN_PROGRESS, _PREFETCH_RESULT, _PREFETCH_COMPLETED_AT
        try:
            result = PriceFetcher().fetch_stock_prices(
                copy.deepcopy(stocks),
                show_progress=False,
                use_cached_history=False,
            )
            with _PREFETCH_LOCK:
                _PREFETCH_RESULT = result
                _PREFETCH_COMPLETED_AT = time_module.time()
        finally:
            with _PREFETCH_LOCK:
                _PREFETCH_IN_PROGRESS = False

    thread = threading.Thread(target=_worker, name="stock-price-prefetch", daemon=True)
    thread.start()
    return "started"


def get_prefetched_stock_prices(max_age_seconds: int = 300) -> Optional[Tuple[List[Dict], List[str]]]:
    """Return a copy of the warmed price result if it is still fresh."""
    with _PREFETCH_LOCK:
        if _PREFETCH_RESULT is None:
            return None
        if time_module.time() - _PREFETCH_COMPLETED_AT > max_age_seconds:
            return None
        return copy.deepcopy(_PREFETCH_RESULT)


def clear_stock_price_prefetch():
    """Clear the background price cache, used when the user explicitly refreshes."""
    global _PREFETCH_RESULT, _PREFETCH_COMPLETED_AT
    with _PREFETCH_LOCK:
        _PREFETCH_RESULT = None
        _PREFETCH_COMPLETED_AT = 0.0

class PriceFetcher:
    def __init__(self):
        self.failed_symbols = []
        
    def fetch_stock_prices(
        self,
        stocks: List[Dict],
        language: str = 'en',
        show_progress: bool = True,
        use_cached_history: bool = True,
    ) -> Tuple[List[Dict], List[str]]:
        """
        Fetch current stock prices using yfinance
        Returns updated stocks list and list of symbols that failed to fetch
        """
        updated_stocks = []
        failed_symbols = []
        
        progress_container = None
        progress_bar = None
        status_text = None

        if show_progress:
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
            
        non_cash_stocks = [s for s in stocks if s.get("symbol") != "CASH"]
        total_stocks = len(non_cash_stocks)
        
        for i, stock in enumerate(stocks):
            symbol = stock.get("symbol")
            
            # Skip cash
            if symbol == "CASH":
                updated_stocks.append(stock.copy())
                continue

            # Corporate-action claims can have a known fixed settlement value
            # without a tradeable market ticker. They are valid positions, not
            # failed price downloads.
            if stock.get("price_mode") == "fixed":
                updated_stock = stock.copy()
                updated_stock["current_price"] = stock["price"]
                updated_stock["previous_close"] = stock["price"]
                updated_stock["display_currency"] = "EUR"
                updated_stock["price_source"] = "fixed"
                updated_stocks.append(updated_stock)
                current_progress = len([
                    item for item in updated_stocks
                    if item.get("symbol") != "CASH"
                ])
                if progress_bar:
                    progress_bar.progress(current_progress / total_stocks)
                continue
                
            current_index = len([s for s in updated_stocks if s.get("symbol") != "CASH"])
            display_symbol = symbol or stock.get("wkn") or stock.get("name", "Unknown")
            
            if status_text:
                status_text.text(f"{get_text('fetching_price_for', language, display_symbol)} ({current_index + 1}/{total_stocks})")
            
            try:
                # Fetch enough history for a real previous close. Prices returned
                # here are already EUR per legal portfolio unit.
                hist = fetch_stock_history_eur(
                    stock,
                    period="5d",
                    use_cache=use_cached_history,
                )
                
                if not hist.empty:
                    # Get current and previous closing prices
                    current_price = float(hist['Close'].iloc[-1])
                    
                    # Get previous day's close if available
                    previous_close = None
                    if len(hist) > 1:
                        previous_close = float(hist['Close'].iloc[-2])
                    elif 'Open' in hist.columns:
                        previous_close = float(hist['Open'].iloc[-1])
                    
                    # Update stock with current price
                    updated_stock = stock.copy()
                    updated_stock['current_price'] = current_price
                    updated_stock['previous_close'] = previous_close
                    updated_stock['display_currency'] = 'EUR'
                    updated_stock['price_source'] = 'live'
                    updated_stocks.append(updated_stock)
                else:
                    # No data available, use default price
                    updated_stock = stock.copy()
                    updated_stock['current_price'] = stock['price']
                    updated_stock['previous_close'] = stock['price']  # No change data
                    updated_stock['price_source'] = 'default'
                    updated_stocks.append(updated_stock)
                    failed_symbols.append(display_symbol)
                    
            except Exception as e:
                # Error fetching data, use default price
                updated_stock = stock.copy()
                updated_stock['current_price'] = stock['price']
                updated_stock['previous_close'] = stock['price']  # No change data
                updated_stock['price_source'] = 'default'
                updated_stocks.append(updated_stock)
                failed_symbols.append(display_symbol)
                
            # Update progress bar
            current_progress = len([s for s in updated_stocks if s.get("symbol") != "CASH"])
            progress_percentage = current_progress / total_stocks
            if progress_bar:
                progress_bar.progress(progress_percentage)
            
        # Remove all loading UI as soon as the final quote is available.
        if progress_bar:
            progress_bar.empty()
        if status_text:
            status_text.empty()
        if progress_container:
            progress_container.empty()
        
        return updated_stocks, failed_symbols
    
    def get_portfolio_value(self, stocks: List[Dict]) -> float:
        """Calculate total portfolio value"""
        total_value = 0
        for stock in stocks:
            current_price = stock.get('current_price', stock['price'])
            total_value += stock['quantity'] * current_price
        return total_value
    
    def get_stock_value(self, stock: Dict) -> float:
        """Get individual stock total value"""
        current_price = stock.get('current_price', stock['price'])
        return stock['quantity'] * current_price
    
    def get_price_change_percentage(self, stock: Dict) -> float:
        """Calculate price change percentage from default to current"""
        if stock.get('price_source') == 'default':
            return 0.0
        
        current_price = stock.get('current_price', stock['price'])
        original_price = stock['price']
        
        if original_price == 0:
            return 0.0
            
        return ((current_price - original_price) / original_price) * 100
    
    def get_daily_change_percentage(self, stock: Dict) -> float:
        """Calculate daily price change percentage"""
        current_price = stock.get('current_price', stock['price'])
        previous_close = stock.get('previous_close')
        
        if previous_close is None or previous_close == 0:
            return 0.0
            
        return ((current_price - previous_close) / previous_close) * 100
    
    def get_user_daily_change_value(self, stock: Dict, user_percentage: float) -> float:
        """Calculate daily value change for user's portion"""
        current_price = stock.get('current_price', stock['price'])
        previous_close = stock.get('previous_close')
        
        if previous_close is None:
            return 0.0
            
        daily_change = (current_price - previous_close) * stock['quantity'] * user_percentage
        return daily_change
    
    def get_historical_data(self, stocks: List[Dict], period: str = '1d') -> List[Dict]:
        """Get historical data for stocks for the specified period"""
        period_map = {
            '1d': '2d',  # Need 2 days to calculate 1-day change
            '1w': '1wk',
            '1m': '1mo', 
            '1y': '1y'
        }
        
        yf_period = period_map.get(period, '2d')
        updated_stocks = []
        
        for stock in stocks:
            if stock.get('symbol') == 'CASH':
                updated_stock = stock.copy()
                updated_stock['historical_change'] = 0.0
                updated_stock['period'] = period
                updated_stocks.append(updated_stock)
                continue
                
            try:
                hist = fetch_stock_history_eur(stock, period=yf_period)
                
                if not hist.empty and len(hist) >= 2:
                    current_price = float(hist['Close'].iloc[-1])
                    
                    if period == '1d':
                        # For 1-day, use previous day's close or today's open
                        if len(hist) > 1:
                            previous_price = float(hist['Close'].iloc[-2])
                        else:
                            previous_price = float(hist['Open'].iloc[-1])
                    else:
                        # For longer periods, use first day's close
                        previous_price = float(hist['Close'].iloc[0])
                    
                    change_percentage = ((current_price - previous_price) / previous_price * 100) if previous_price > 0 else 0
                    
                    updated_stock = stock.copy()
                    updated_stock['current_price'] = current_price
                    updated_stock['previous_price'] = previous_price
                    updated_stock['historical_change'] = change_percentage
                    updated_stock['period'] = period
                    updated_stock['price_source'] = 'live'
                    updated_stocks.append(updated_stock)
                else:
                    # Fallback to default
                    updated_stock = stock.copy()
                    updated_stock['current_price'] = stock['price']
                    updated_stock['previous_price'] = stock['price']
                    updated_stock['historical_change'] = 0.0
                    updated_stock['period'] = period
                    updated_stock['price_source'] = 'default'
                    updated_stocks.append(updated_stock)
                    
            except Exception as e:
                # Error fetching data
                updated_stock = stock.copy()
                updated_stock['current_price'] = stock['price']
                updated_stock['previous_price'] = stock['price']
                updated_stock['historical_change'] = 0.0
                updated_stock['period'] = period
                updated_stock['price_source'] = 'default'
                updated_stocks.append(updated_stock)
        
        return updated_stocks

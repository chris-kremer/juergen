"""
Stock price fetching functionality with fallback to default values
"""

import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Dict, List, Tuple
import time
from translations import get_language, get_text, format_currency, format_currency_change

class PriceFetcher:
    def __init__(self):
        self.failed_symbols = []
        
    def fetch_stock_prices(self, stocks: List[Dict], language: str = 'en') -> Tuple[List[Dict], List[str]]:
        """
        Fetch current stock prices using yfinance
        Returns updated stocks list and list of symbols that failed to fetch
        """
        updated_stocks = []
        failed_symbols = []
        
        # Simple progress display
        progress_container = st.container()
        
        with progress_container:
            # Progress bar
            progress_bar = st.progress(0)
            # Simple status text
            status_text = st.empty()
            
        non_cash_stocks = [s for s in stocks if s["symbol"] != "CASH"]
        total_stocks = len(non_cash_stocks)
        
        for i, stock in enumerate(stocks):
            symbol = stock["symbol"]
            
            # Skip cash
            if symbol == "CASH":
                updated_stocks.append(stock.copy())
                continue
                
            current_index = len([s for s in updated_stocks if s["symbol"] != "CASH"])
            
            # Update status
            status_text.text(f"{get_text('fetching_price_for', language, symbol)} ({current_index + 1}/{total_stocks})")
            
            try:
                # Fetch stock data
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                
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
                    updated_stock['price_source'] = 'live'
                    updated_stocks.append(updated_stock)
                else:
                    # No data available, use default price
                    updated_stock = stock.copy()
                    updated_stock['current_price'] = stock['price']
                    updated_stock['previous_close'] = stock['price']  # No change data
                    updated_stock['price_source'] = 'default'
                    updated_stocks.append(updated_stock)
                    failed_symbols.append(symbol)
                    
            except Exception as e:
                # Error fetching data, use default price
                updated_stock = stock.copy()
                updated_stock['current_price'] = stock['price']
                updated_stock['previous_close'] = stock['price']  # No change data
                updated_stock['price_source'] = 'default'
                updated_stocks.append(updated_stock)
                failed_symbols.append(symbol)
                
            # Update progress bar
            current_progress = len([s for s in updated_stocks if s["symbol"] != "CASH"])
            progress_percentage = current_progress / total_stocks
            progress_bar.progress(progress_percentage)
            
            # Small delay to avoid hitting rate limits
            time.sleep(0.1)
        
        # Keep completed status briefly then clear
        status_text.text(f"✅ Completed! ({total_stocks}/{total_stocks})")
        time.sleep(1.0)
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
            if stock['symbol'] == 'CASH':
                updated_stock = stock.copy()
                updated_stock['historical_change'] = 0.0
                updated_stock['period'] = period
                updated_stocks.append(updated_stock)
                continue
                
            try:
                ticker = yf.Ticker(stock['symbol'])
                hist = ticker.history(period=yf_period)
                
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

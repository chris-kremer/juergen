"""
Stock Portfolio Overview Application
A Streamlit app for managing and viewing a shared stock portfolio
"""

import streamlit as st
from auth import AuthSystem
from price_fetcher import (
    PriceFetcher,
    clear_stock_price_prefetch,
    get_prefetched_stock_prices,
    start_stock_price_prefetch,
)
from portfolio_dashboard import PortfolioDashboard
from config import STOCKS
from ownership import get_user_portfolio_value
from translations import get_language, get_text
from message_system import message_system
from ui_theme import build_app_css, build_footer

# Page configuration
st.set_page_config(
    page_title="Portfolio Overview",
    page_icon="↗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for a calmer dashboard presentation
st.markdown("""
<style>
    :root {
        --app-bg: #f6f8fb;
        --panel-bg: #ffffff;
        --border: #e4e9f0;
        --muted: #667085;
        --text: #182230;
        --accent: #2563eb;
    }

    .stApp {
        background: var(--app-bg);
    }

    .block-container {
        max-width: 1420px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: var(--panel-bg);
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: var(--muted);
        line-height: 1.45;
    }

    h1, h2, h3 {
        color: var(--text);
        letter-spacing: 0;
    }

    h1 {
        font-size: 2rem;
        margin-bottom: 0.25rem;
    }

    h2, h3 {
        margin-top: 1.25rem;
    }

    hr {
        margin: 1.25rem 0;
        border-color: var(--border);
    }

    [data-testid="stMetric"] {
        background: var(--panel-bg);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1rem 1rem 0.9rem;
        min-height: 112px;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted);
    }

    [data-testid="stMetricValue"] {
        color: var(--text);
        font-weight: 700;
        font-size: 1.55rem;
    }

    [data-testid="stMetricDelta"] {
        font-weight: 600;
    }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 0.85rem;
        margin: 0.75rem 0 1.25rem;
    }

    .metric-card {
        background: var(--panel-bg);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1rem;
        min-height: 112px;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
    }

    .metric-label {
        color: var(--muted);
        font-size: 0.82rem;
        line-height: 1.25;
        margin-bottom: 0.55rem;
        white-space: normal;
    }

    .metric-value {
        color: var(--text);
        font-size: 1.45rem;
        font-weight: 750;
        line-height: 1.15;
        overflow-wrap: anywhere;
    }

    .metric-delta {
        font-size: 0.9rem;
        font-weight: 650;
        margin-top: 0.5rem;
    }

    .metric-delta.positive {
        color: #16a34a;
    }

    .metric-delta.negative {
        color: #dc2626;
    }

    .metric-delta.neutral {
        color: var(--muted);
    }

    [data-testid="stPlotlyChart"],
    [data-testid="stDataFrame"] {
        background: var(--panel-bg);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.75rem;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
    }

    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid var(--border);
        font-weight: 600;
        color: var(--text);
        background: var(--panel-bg);
    }

    .stButton > button p {
        color: inherit;
    }

    .stButton > button[kind="primary"],
    .stDownloadButton > button {
        border-radius: 8px;
    }

    div[data-testid="stAlert"] {
        border-radius: 8px;
        border: 1px solid var(--border);
    }
</style>
""", unsafe_allow_html=True)

# Refined visual layer: quieter Streamlit chrome and an editorial fintech feel.
st.markdown(f"<style>{build_app_css()}</style>", unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Initialize components
    auth = AuthSystem()
    price_fetcher = PriceFetcher()
    dashboard = PortfolioDashboard(price_fetcher)
    
    # Check authentication
    if not auth.is_authenticated():
        start_stock_price_prefetch(STOCKS)
        auth.show_login_form()
        return
    
    # User is authenticated - show dashboard
    user = auth.get_current_user()
    auth.show_user_info()
    
    # Main content area
    if user:
        lang = get_language(user['username'])
        
        # Add refresh button in sidebar
        with st.sidebar:
            st.markdown("---")
            if st.button(get_text('refresh_prices', lang), use_container_width=True):
                st.cache_data.clear()
                clear_stock_price_prefetch()
                st.rerun()
            
            st.markdown("---")
            st.markdown(f"### {get_text('portfolio_info', lang)}")
            st.markdown(get_text('portfolio_description', lang))
            st.markdown(get_text('price_info', lang))
        
        # Fetch stock prices (with caching for better performance)
        @st.cache_data(ttl=300)  # Cache for 5 minutes
        def fetch_prices(language):
            warmed_prices = get_prefetched_stock_prices()
            if warmed_prices is not None:
                return warmed_prices
            return price_fetcher.fetch_stock_prices(STOCKS, language)
        
        # Show loading message
        with st.spinner(get_text('fetching_prices', lang)):
            stocks_with_prices, failed_symbols = fetch_prices(lang)
        # A cached Yahoo response can contain NaN for the newest candle. Repair
        # it before any dashboard calculation, even if the cache predates the
        # current quote-validation code.
        stocks_with_prices, repaired_symbols = price_fetcher.sanitize_stock_prices(
            stocks_with_prices
        )
        failed_symbols = list(dict.fromkeys([*failed_symbols, *repaired_symbols]))
        
        # Calculate current portfolio value for messages
        total_portfolio_value = price_fetcher.get_portfolio_value(stocks_with_prices)
        user_portfolio_value = get_user_portfolio_value(
            user['username'],
            total_portfolio_value,
        )
        
        # Show user messages (weekend, value changes, one-time messages)
        message_system.show_messages(user['username'], user_portfolio_value)
        
        # Display dashboard
        dashboard.show_dashboard(user, stocks_with_prices, failed_symbols)
        
        # Quiet branded footer
        st.markdown(build_footer(lang), unsafe_allow_html=True)

if __name__ == "__main__":
    main()

"""
Stock Portfolio Overview Application
A Streamlit app for managing and viewing a shared stock portfolio
"""

import streamlit as st
from auth import AuthSystem
from price_fetcher import PriceFetcher
from portfolio_dashboard import PortfolioDashboard
from config import STOCKS
from translations import get_language, get_text
from message_system import message_system

# Page configuration
st.set_page_config(
    page_title="Portfolio Overview",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        padding: 1rem 0;
        border-bottom: 2px solid #f0f2f6;
        margin-bottom: 2rem;
    }
    
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    
    .login-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        border-radius: 1rem;
        border: 1px solid #e1e5e9;
        background-color: #f8f9fa;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Initialize components
    auth = AuthSystem()
    price_fetcher = PriceFetcher()
    dashboard = PortfolioDashboard(price_fetcher)
    
    # Check authentication
    if not auth.is_authenticated():
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
                st.rerun()
            
            st.markdown("---")
            st.markdown(f"### {get_text('portfolio_info', lang)}")
            st.markdown(get_text('portfolio_description', lang))
            st.markdown(get_text('price_info', lang))
        
        # Fetch stock prices (with caching for better performance)
        @st.cache_data(ttl=300)  # Cache for 5 minutes
        def fetch_prices(language):
            return price_fetcher.fetch_stock_prices(STOCKS, language)
        
        # Show loading message
        with st.spinner(get_text('fetching_prices', lang)):
            stocks_with_prices, failed_symbols = fetch_prices(lang)
        
        # Calculate current portfolio value for messages
        total_portfolio_value = price_fetcher.get_portfolio_value(stocks_with_prices)
        user_portfolio_value = total_portfolio_value * user['portfolio_percentage']
        
        # Show user messages (weekend, value changes, one-time messages)
        message_system.show_messages(user['username'], user_portfolio_value)
        
        # Display dashboard
        dashboard.show_dashboard(user, stocks_with_prices, failed_symbols)
        
        # Footer
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                f"""
                <div style='text-align: center; color: #666; font-size: 0.8rem;'>
                📊 {get_text('portfolio_app', lang)}<br>
                {get_text('data_disclaimer', lang)}
                </div>
                """, 
                unsafe_allow_html=True
            )

if __name__ == "__main__":
    main()

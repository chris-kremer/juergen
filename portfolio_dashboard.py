"""
Portfolio dashboard for displaying user's portfolio overview
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict
from price_fetcher import PriceFetcher
from config import STOCKS
from translations import get_language, get_text, format_currency, format_currency_change

class PortfolioDashboard:
    def __init__(self, price_fetcher: PriceFetcher):
        self.price_fetcher = price_fetcher
    
    def show_dashboard(self, user: Dict, stocks_with_prices: List[Dict], failed_symbols: List[str]):
        """Display the main portfolio dashboard"""
        
        lang = get_language(user['username'])
        
        # Dashboard header
        st.title(get_text('portfolio_overview', lang, user['username'].title()))
        st.markdown("---")
        
        # Show price fetch status
        if failed_symbols:
            with st.expander(get_text('price_fetch_status', lang), expanded=False):
                st.warning(get_text('could_not_fetch', lang, len(failed_symbols)))
                for symbol in failed_symbols:
                    st.text(f"• {symbol}")
        
        # Calculate portfolio metrics
        total_portfolio_value = self.price_fetcher.get_portfolio_value(stocks_with_prices)
        user_portfolio_value = total_portfolio_value * user['portfolio_percentage']
        
        # Calculate returns and daily changes
        initial_investment = user.get('initial_investment', 0)
        total_return_amount = user_portfolio_value - initial_investment
        total_return_percentage = (total_return_amount / initial_investment * 100) if initial_investment > 0 else 0
        
        # Calculate total daily change
        total_daily_change = sum([
            self.price_fetcher.get_user_daily_change_value(stock, user['portfolio_percentage'])
            for stock in stocks_with_prices
        ])
        
        # Calculate daily percentage change
        daily_percentage = (total_daily_change / user_portfolio_value * 100) if user_portfolio_value > 0 else 0
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label=get_text('your_portfolio_value', lang),
                value=format_currency(user_portfolio_value, lang),
                delta=None
            )
        
        with col2:
            st.metric(
                label=get_text('total_return', lang),
                value=format_currency_change(total_return_amount, lang),
                delta=f"{total_return_percentage:+.1f}%" if total_return_percentage != 0 else None
            )
        
        with col3:
            st.metric(
                label=get_text('daily_change', lang),
                value=format_currency_change(total_daily_change, lang),
                delta=f"{daily_percentage:+.2f}%" if daily_percentage != 0 else None
            )
        
        with col4:
            live_count = len([s for s in stocks_with_prices if s.get('price_source') == 'live'])
            st.metric(
                label=get_text('live_prices', lang),
                value=f"{live_count}/{len(stocks_with_prices)-1}",  # -1 for cash
                delta=None
            )
        
        st.markdown("---")
        
        # Multi-period returns chart
        self.show_returns_chart(user, lang)
        
        st.markdown("---")
        
        # Portfolio breakdown charts
        self.show_portfolio_breakdown(stocks_with_prices, user, lang)
        
        # Detailed holdings table
        self.show_holdings_table(stocks_with_prices, user, lang)
    
    def show_returns_chart(self, user: Dict, lang: str):
        """Show position returns chart with time period selector"""
        
        st.subheader(get_text('position_returns', lang))
        
        # Time period selector
        col1, col2 = st.columns([3, 1])
        
        with col2:
            period_options = ['1d', '1w', '1m', '1y']
            period_labels = {
                '1d': get_text('period_1d', lang),
                '1w': get_text('period_1w', lang), 
                '1m': get_text('period_1m', lang),
                '1y': get_text('period_1y', lang)
            }
            
            selected_period = st.selectbox(
                "Period",
                period_options,
                index=3,  # Default to 1y (index 3)
                format_func=lambda x: period_labels[x],
                key="returns_period"
            )
        
        # Fetch historical data for selected period
        with st.spinner(f"Loading {period_labels[selected_period]} data..."):
            historical_stocks = self.price_fetcher.get_historical_data(STOCKS, selected_period)
        
        # Prepare data for chart
        returns_data = []
        for stock in historical_stocks:
            if stock['symbol'] == 'CASH':  # Skip cash
                continue
                
            change_percentage = stock.get('historical_change', 0)
            
            # Only include positions with meaningful changes or if they have live prices
            if abs(change_percentage) > 0.01 or stock.get('price_source') == 'live':
                returns_data.append({
                    'Symbol': stock['symbol'],
                    'Name': stock['name'],
                    'Return (%)': change_percentage,
                    'Color': '#00AA00' if change_percentage >= 0 else '#FF4444'  # Solid green/red
                })
        
        if returns_data:
            # Sort by return percentage (highest gain to highest loss)
            returns_data.sort(key=lambda x: x['Return (%)'], reverse=True)
            
            df = pd.DataFrame(returns_data)
            
            # Create the bar chart
            fig = px.bar(
                df,
                x='Symbol',
                y='Return (%)',
                title=f"{get_text('position_returns', lang)} - {period_labels[selected_period]}",
                color='Color',
                color_discrete_map='identity',  # Use the colors as provided
                hover_data={
                    'Name': True,
                    'Return (%)': ':.2f'
                }
            )
            
            # Customize the chart
            fig.update_layout(
                xaxis_title="",
                yaxis_title="Return (%)",
                showlegend=False,
                height=400,
                xaxis_tickangle=-45
            )
            
            # Add zero line
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary stats
            winners = len([x for x in returns_data if x['Return (%)'] > 0])
            losers = len([x for x in returns_data if x['Return (%)'] < 0])
            unchanged = len([x for x in returns_data if x['Return (%)'] == 0])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Gainers", winners, delta=None)
            with col2:
                st.metric("Losers", losers, delta=None)  
            with col3:
                st.metric("Unchanged", unchanged, delta=None)
        else:
            st.info(f"No {period_labels[selected_period].lower()} data available (all using default prices)")
    
    def show_portfolio_breakdown(self, stocks: List[Dict], user: Dict, lang: str):
        """Show portfolio breakdown charts"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(get_text('portfolio_allocation', lang))
            
            # Prepare data for pie chart
            chart_data = []
            for stock in stocks:
                value = self.price_fetcher.get_stock_value(stock) * user['portfolio_percentage']
                if value > 0:  # Only show non-zero values
                    chart_data.append({
                        'Symbol': stock['symbol'],
                        'Name': stock['name'],
                        'Value': value,
                        'Industry': stock.get('industry', 'Other')
                    })
            
            df = pd.DataFrame(chart_data)
            
            if not df.empty:
                fig = px.pie(
                    df, 
                    values='Value', 
                    names='Symbol',
                    hover_data=['Name', 'Industry'],
                    title=get_text('holdings_distribution', lang)
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader(get_text('industry_breakdown', lang))
            
            # Group by industry
            industry_data = {}
            for stock in stocks:
                industry = stock.get('industry', 'Other')
                if industry is None:
                    industry = 'Cash'
                value = self.price_fetcher.get_stock_value(stock) * user['portfolio_percentage']
                
                if industry in industry_data:
                    industry_data[industry] += value
                else:
                    industry_data[industry] = value
            
            industry_df = pd.DataFrame([
                {'Industry': k, 'Value': v} 
                for k, v in industry_data.items() 
                if v > 0
            ])
            
            if not industry_df.empty:
                fig = px.bar(
                    industry_df, 
                    x='Industry', 
                    y='Value',
                    title=get_text('holdings_by_industry', lang)
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
    
    def show_holdings_table(self, stocks: List[Dict], user: Dict, lang: str):
        """Show detailed holdings table"""
        
        st.subheader(get_text('detailed_holdings', lang))
        
        # Prepare table data
        table_data = []
        for stock in stocks:
            current_price = stock.get('current_price', stock['price'])
            your_quantity = stock['quantity'] * user['portfolio_percentage']
            your_value = your_quantity * current_price
            price_change = self.price_fetcher.get_price_change_percentage(stock)
            daily_change_pct = self.price_fetcher.get_daily_change_percentage(stock)
            
            industry = stock.get('industry', 'N/A')
            # Translate industry names
            if industry:
                industry = get_text(industry, lang)
            
            table_data.append({
                get_text('symbol', lang): stock['symbol'],
                get_text('name', lang): stock['name'],
                get_text('industry', lang): industry,
                get_text('your_quantity', lang): your_quantity,
                get_text('current_price', lang): current_price,
                get_text('your_value', lang): your_value,
                get_text('daily_change', lang): f"{daily_change_pct:+.2f}%",
                get_text('price_source', lang): stock.get('price_source', 'default').title()
            })
        
        df = pd.DataFrame(table_data)
        
        # Sort by value descending
        df = df.sort_values(get_text('your_value', lang), ascending=False)
        
        # Format the dataframe for display
        formatted_df = df.copy()
        your_quantity_col = get_text('your_quantity', lang)
        current_price_col = get_text('current_price', lang)
        your_value_col = get_text('your_value', lang)
        daily_change_col = get_text('daily_change', lang)
        
        formatted_df[your_quantity_col] = formatted_df[your_quantity_col].apply(lambda x: f"{x:.2f}" if x < 1000 else f"{x:,.0f}")
        formatted_df[current_price_col] = formatted_df[current_price_col].apply(lambda x: format_currency(x, lang))
        formatted_df[your_value_col] = formatted_df[your_value_col].apply(lambda x: format_currency(x, lang))
        # Daily change is already formatted
        
        # Style the dataframe
        def color_daily_change(val):
            if '0.00%' in str(val) or 'N/A' in str(val):
                return 'color: gray'
            elif '+' in str(val):
                return 'color: green'
            else:
                return 'color: red'
        
        styled_df = formatted_df.style.applymap(color_daily_change, subset=[daily_change_col])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_positions = len([s for s in stocks if s['symbol'] != 'CASH'])
            st.metric(get_text('total_positions', lang), total_positions)
        
        with col2:
            cash_value = next((self.price_fetcher.get_stock_value(s) * user['portfolio_percentage'] 
                             for s in stocks if s['symbol'] == 'CASH'), 0)
            st.metric(get_text('cash_position', lang), format_currency(cash_value, lang))
        
        with col3:
            live_prices = len([s for s in stocks if s.get('price_source') == 'live'])
            total_non_cash = len([s for s in stocks if s['symbol'] != 'CASH'])
            st.metric(get_text('live_price_coverage', lang), f"{live_prices}/{total_non_cash}")

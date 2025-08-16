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
        
        # Show user overview if this is the "user" account
        if user['username'] == 'user':
            self.show_all_users_overview(stocks_with_prices, lang)
            st.markdown("---")
        
        # Historical portfolio performance chart
        self.show_historical_performance_chart(user, lang)
        
        st.markdown("---")
        
        # Multi-period returns chart
        self.show_returns_chart(user, lang)
        
        st.markdown("---")
        
        # Portfolio breakdown charts
        self.show_portfolio_breakdown(stocks_with_prices, user, lang)
        
        # Detailed holdings table
        self.show_holdings_table(stocks_with_prices, user, lang)
    
    def show_all_users_overview(self, stocks_with_prices: List[Dict], lang: str):
        """Show overview of all users' portfolio values (only for 'user' account)"""
        from config import USERS
        
        st.subheader(get_text('all_users_overview', lang))
        
        # Calculate total portfolio value
        total_portfolio_value = self.price_fetcher.get_portfolio_value(stocks_with_prices)
        
        # Prepare data for all users
        user_data = []
        for user_info in USERS:
            if user_info['username'] != 'user':  # Skip the overview user itself
                user_value = total_portfolio_value * user_info['portfolio_percentage']
                initial_investment = user_info.get('initial_investment', 0)
                total_return = user_value - initial_investment
                return_percentage = (total_return / initial_investment * 100) if initial_investment > 0 else 0
                
                user_data.append({
                    'User': user_info['username'].title(),
                    'Portfolio Value': user_value,
                    'Initial Investment': initial_investment,
                    'Total Return': total_return,
                    'Return %': return_percentage,
                    'Share %': user_info['portfolio_percentage'] * 100
                })
        
        # Sort by portfolio value descending
        user_data.sort(key=lambda x: x['Portfolio Value'], reverse=True)
        
        # Create DataFrame
        df = pd.DataFrame(user_data)
        
        # Format for display
        formatted_df = df.copy()
        formatted_df['Portfolio Value'] = formatted_df['Portfolio Value'].apply(lambda x: format_currency(x, lang))
        formatted_df['Initial Investment'] = formatted_df['Initial Investment'].apply(lambda x: format_currency(x, lang))
        formatted_df['Total Return'] = formatted_df['Total Return'].apply(lambda x: format_currency_change(x, lang))
        formatted_df['Return %'] = formatted_df['Return %'].apply(lambda x: f"{x:+.1f}%")
        formatted_df['Share %'] = formatted_df['Share %'].apply(lambda x: f"{x:.1f}%")
        
        # Style the dataframe
        def color_returns(val):
            if '+' in str(val):
                return 'color: green'
            elif '-' in str(val):
                return 'color: red'
            else:
                return 'color: gray'
        
        styled_df = formatted_df.style.map(color_returns, subset=['Total Return', 'Return %'])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_users = len(user_data)
            st.metric("Active Users", total_users)
        
        with col2:
            total_invested = sum([u['Initial Investment'] for u in user_data])
            st.metric("Total Invested", format_currency(total_invested, lang))
        
        with col3:
            current_total = sum([u['Portfolio Value'] for u in user_data])
            st.metric("Current Total", format_currency(current_total, lang))
    
    def show_historical_performance_chart(self, user: Dict, lang: str):
        """Show historical portfolio performance vs URTH benchmark with progressive loading"""
        
        st.subheader(get_text('historical_performance', lang))
        
        # Create containers for dynamic updates
        chart_container = st.empty()
        progress_container = st.empty()
        metrics_container = st.empty()
        
        # Initialize dates for 6 months
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        # Create sample dates (monthly intervals)
        sample_dates = []
        current_date = start_date
        while current_date <= end_date:
            sample_dates.append(current_date)
            current_date += timedelta(days=30)
        
        # Initialize chart with all values at 100
        initial_portfolio_values = [100] * len(sample_dates)
        initial_urth_values = [100] * len(sample_dates)
        
        # Create initial chart
        fig = go.Figure()
        
        portfolio_trace = fig.add_trace(go.Scatter(
            x=sample_dates,
            y=initial_portfolio_values,
            mode='lines',
            name='Your Portfolio',
            line=dict(color='#1f77b4', width=3)
        ))
        
        urth_trace = fig.add_trace(go.Scatter(
            x=sample_dates,
            y=initial_urth_values,
            mode='lines',
            name='URTH Benchmark',
            line=dict(color='#ff7f0e', width=2, dash='dash')
        ))
        
        # Add baseline at 100
        fig.add_hline(
            y=100, 
            line_dash="dot", 
            line_color="gray", 
            opacity=0.5,
            annotation_text="Baseline (100)"
        )
        
        # Customize layout
        fig.update_layout(
            title=get_text('portfolio_vs_benchmark', lang),
            xaxis_title="Date",
            yaxis_title=get_text('relative_performance', lang),
            height=400,
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left", 
                x=0.01
            )
        )
        
        # Show initial chart
        with chart_container.container():
            st.plotly_chart(fig, use_container_width=True, key="historical_chart")
        
        # Initialize arrays for progressive loading
        portfolio_values = [100] * len(sample_dates)
        urth_values = [100] * len(sample_dates)
        
        # Progressive data loading
        total_points = len(sample_dates)
        
        with progress_container.container():
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        # Load data for each date progressively
        for i, date in enumerate(sample_dates):
            status_text.text(f"Loading data for {date.strftime('%B %Y')}... ({i+1}/{total_points})")
            
            # Get real data for this date
            portfolio_value, urth_value = self._get_single_date_data(date, user)
            
            # Store the actual values
            if i == 0:
                # First point establishes the base
                portfolio_base = portfolio_value
                urth_base = urth_value
                portfolio_values[i] = 100
                urth_values[i] = 100
            else:
                # Calculate relative values
                portfolio_values[i] = (portfolio_value / portfolio_base) * 100 if portfolio_base > 0 else 100
                urth_values[i] = (urth_value / urth_base) * 100 if urth_base > 0 else 100
            
            # Update chart
            fig.data[0].y = portfolio_values[:i+1] + [100] * (len(sample_dates) - i - 1)
            fig.data[1].y = urth_values[:i+1] + [100] * (len(sample_dates) - i - 1)
            
            # Update the chart display
            with chart_container.container():
                st.plotly_chart(fig, use_container_width=True, key=f"historical_chart_{i}")
            
            # Update progress
            progress_bar.progress((i + 1) / total_points)
            
            # Small delay for visual effect
            import time
            time.sleep(0.3)
        
        # Final update with complete data
        fig.data[0].y = portfolio_values
        fig.data[1].y = urth_values
        
        with chart_container.container():
            st.plotly_chart(fig, use_container_width=True, key="historical_chart_final")
        
        # Clear progress indicators
        progress_container.empty()
        
        # Show final metrics
        if len(portfolio_values) > 1:
            portfolio_change = portfolio_values[-1] - 100
            urth_change = urth_values[-1] - 100
            
            with metrics_container.container():
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Your Performance", 
                        f"{portfolio_values[-1]:.1f}",
                        f"{portfolio_change:+.1f}"
                    )
                
                with col2:
                    st.metric(
                        "URTH Performance", 
                        f"{urth_values[-1]:.1f}",
                        f"{urth_change:+.1f}"
                    )
                
                with col3:
                    outperformance = portfolio_change - urth_change
                    st.metric(
                        "Outperformance",
                        f"{outperformance:+.1f}",
                        delta_color="normal" if outperformance >= 0 else "inverse"
                    )
    
    def _get_single_date_data(self, date, user):
        """Get portfolio and URTH values for a single date"""
        try:
            import yfinance as yf
            from datetime import timedelta
            
            total_portfolio_value = 0
            urth_price = None
            
            # Get data for each stock on this date
            for stock in STOCKS:
                if stock['symbol'] == 'CASH':
                    total_portfolio_value += stock['quantity'] * 1.0
                    continue
                
                try:
                    ticker = yf.Ticker(stock['symbol'])
                    # Get data around this date
                    hist = ticker.history(start=date - timedelta(days=5), end=date + timedelta(days=5))
                    
                    if not hist.empty:
                        # Use the closest available price
                        price = float(hist['Close'].iloc[-1])
                    else:
                        # Fallback to default price
                        price = stock['price']
                    
                    if stock['symbol'] == 'URTH':
                        urth_price = price
                    
                    total_portfolio_value += stock['quantity'] * price
                    
                except:
                    # Use default price if error
                    price = stock['price']
                    if stock['symbol'] == 'URTH':
                        urth_price = price
                    total_portfolio_value += stock['quantity'] * price
            
            # Calculate user's portfolio value
            user_portfolio_value = total_portfolio_value * user['portfolio_percentage']
            
            # If no URTH price found, use default
            if urth_price is None:
                urth_price = next((s['price'] for s in STOCKS if s['symbol'] == 'URTH'), 100)
            
            return user_portfolio_value, urth_price
            
        except Exception as e:
            # Return default values on error
            default_portfolio = sum(s['quantity'] * s['price'] for s in STOCKS) * user['portfolio_percentage']
            default_urth = next((s['price'] for s in STOCKS if s['symbol'] == 'URTH'), 100)
            return default_portfolio, default_urth
    
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
                # Special color for URTH (benchmark)
                if stock['symbol'] == 'URTH':
                    color = '#1f77b4'  # Blue for benchmark
                else:
                    color = '#00AA00' if change_percentage >= 0 else '#FF4444'  # Green/red for others
                
                returns_data.append({
                    'Symbol': stock['symbol'],
                    'Name': stock['name'],
                    'Return (%)': change_percentage,
                    'Color': color,
                    'Is_Benchmark': stock['symbol'] == 'URTH'
                })
        
        if returns_data:
            # Separate URTH (benchmark) from other stocks
            urth_data = [x for x in returns_data if x['Symbol'] == 'URTH']
            other_data = [x for x in returns_data if x['Symbol'] != 'URTH']
            
            # Sort other stocks by return percentage (highest gain to highest loss)
            other_data.sort(key=lambda x: x['Return (%)'], reverse=True)
            
            # Put URTH first, then other stocks
            returns_data = urth_data + other_data
            
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
            
            # Add URTH benchmark line
            urth_return = next((item['Return (%)'] for item in returns_data if item['Symbol'] == 'URTH'), None)
            if urth_return is not None:
                fig.add_hline(
                    y=urth_return, 
                    line_dash="dot", 
                    line_color="#1f77b4", 
                    opacity=0.7,
                    annotation_text=f"URTH Benchmark: {urth_return:.1f}%",
                    annotation_position="top right"
                )
            
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
                # Sort by value descending (highest to lowest)
                industry_df = industry_df.sort_values('Value', ascending=False)
                
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
        
        styled_df = formatted_df.style.map(color_daily_change, subset=[daily_change_col])
        
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

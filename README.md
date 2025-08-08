# Stock Portfolio Overview Application

A Streamlit-based web application for viewing and managing a shared stock portfolio with multiple users and real-time price fetching.

## Features

- **Multi-user Authentication**: Secure login system with different portfolio ownership percentages
- **Real-time Stock Prices**: Fetches live prices from Yahoo Finance with fallback to default values
- **Portfolio Dashboard**: Comprehensive overview with charts and metrics
- **Interactive Visualizations**: Pie charts and bar charts for portfolio breakdown
- **Detailed Holdings**: Sortable table with all stock information
- **Price Change Tracking**: Shows price changes from default values
- **Industry Analysis**: Portfolio breakdown by industry sectors

## Users and Access

The application supports the following users with their respective portfolio shares:

| Username | Password | Portfolio Share |
|----------|----------|----------------|
| user | password | 100.00% |
| foehr | foehr1 | 5.90% |
| kremer | kremer1 | 61.45% |
| annika | anakin | 0.32% |
| juergen | juergen1 | 14.75% |
| christian | chris1 | 17.58% |

## Installation & Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   streamlit run app.py
   ```

3. **Access the app**:
   - The app will open in your browser at `http://localhost:8501`
   - Use any of the credentials above to log in

## Application Structure

```
├── app.py                 # Main application file
├── auth.py               # Authentication system
├── config.py             # User and stock configuration
├── price_fetcher.py      # Stock price fetching logic
├── portfolio_dashboard.py # Dashboard and visualization components
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Stock Holdings

The portfolio includes a diverse mix of:
- **Index Funds**: AGIF, EXV1.DE, URTH, DAX, WITR, DBPG
- **Banking**: Citigroup (C), Wells Fargo (WFC), Goldman Sachs (GS)
- **Technology**: Palantir (PLTR)
- **Energy**: BP, Shell (SHEL)
- **Industrial**: Covestro (1COV.DE), Heidelberg Materials (HLBZF)
- **Automotive**: Hyundai (HYMTF)
- **Airlines**: Southwest (LUV), United (UAL)
- **Cash**: Cash reserves

## Key Features Explained

### Price Fetching
- Attempts to fetch live prices from Yahoo Finance for all stocks
- Falls back to default prices if live data is unavailable
- Clearly indicates which prices are live vs. default
- Includes progress indication during price fetching

### Portfolio Calculations
- Each user sees their proportional share of the total portfolio
- Values are calculated based on current prices and user's ownership percentage
- Real-time updates when prices are refreshed

### Dashboard Components
1. **Key Metrics**: Portfolio value, ownership percentage, total portfolio value
2. **Portfolio Allocation**: Pie chart showing distribution by stock
3. **Industry Breakdown**: Bar chart showing holdings by industry
4. **Detailed Holdings**: Comprehensive table with all stock details

### Security
- Simple but secure authentication system
- Session-based login state management
- Logout functionality

## Future Enhancements

The application is designed to be extensible. Potential additions include:
- Historical performance tracking
- Portfolio rebalancing suggestions
- Real-time alerts for significant price changes
- Export functionality for reports
- Mobile-responsive design improvements
- Integration with other data sources

## Technical Notes

- **Caching**: Stock prices are cached for 5 minutes to improve performance
- **Rate Limiting**: Small delays between API calls to respect Yahoo Finance limits
- **Error Handling**: Graceful fallback to default prices when live data fails
- **Responsive Design**: Works on desktop and mobile devices

## Troubleshooting

If you encounter issues:

1. **Price fetching errors**: The app will automatically fall back to default prices
2. **Login issues**: Check that you're using the exact username/password combinations
3. **Performance**: Clear cache using the "Refresh Prices" button if data seems stale
4. **Dependencies**: Ensure all packages in requirements.txt are installed

## Support

For issues or feature requests, please check the application logs in the Streamlit interface.

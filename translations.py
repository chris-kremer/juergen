"""
Language translations for the portfolio application
"""

def get_language(username: str) -> str:
    """Get language preference based on username"""
    german_users = ['juergen', 'kremer']
    return 'de' if username in german_users else 'en'

TRANSLATIONS = {
    'en': {
        # Auth
        'portfolio_login': '🏦 Portfolio Login',
        'please_log_in': 'Please log in to view your portfolio',
        'username': 'Username',
        'password': 'Password',
        'enter_username': 'Enter your username',
        'enter_password': 'Enter your password',
        'login': 'Login',
        'login_successful': 'Login successful!',
        'invalid_credentials': 'Invalid username or password',
        'enter_both': 'Please enter both username and password',
        'welcome': 'Welcome, {}!',
        'portfolio_share': 'Portfolio Share',
        'logout': 'Logout',
        
        # Dashboard
        'portfolio_overview': '📊 Portfolio Overview - {}',
        'price_fetch_status': '⚠️ Price Fetch Status',
        'could_not_fetch': 'Could not fetch live prices for {} symbols. Using default prices:',
        'your_portfolio_value': 'Your Portfolio Value',
        'total_return': 'Total Return',
        'daily_change': 'Daily Change',
        'live_prices': 'Live Prices',
        'daily_moves': 'Daily Position Moves',
        'period_1d': '1 Day',
        'period_1w': '1 Week', 
        'period_1m': '1 Month',
        'period_1y': '1 Year',
        'position_returns': 'Position Returns',
        'all_users_overview': 'All Users Portfolio Overview',
        'user_portfolio_values': 'Portfolio Values by User',
        'historical_performance': 'Historical Portfolio Performance',
        'relative_performance': 'Relative Performance (Base = 100)',
        'portfolio_vs_benchmark': 'Portfolio vs URTH Benchmark',
        'timeframe': 'Timeframe',
        'granularity': 'Granularity',
        'daily': 'Daily',
        'weekly': 'Weekly',
        'monthly': 'Monthly',
        'period_3m': '3 Months',
        'period_6m': '6 Months',
        'portfolio_allocation': 'Portfolio Allocation',
        'holdings_distribution': 'Your Holdings Distribution',
        'industry_breakdown': 'Industry Breakdown',
        'holdings_by_industry': 'Your Holdings by Industry',
        'detailed_holdings': 'Detailed Holdings',
        'symbol': 'Symbol',
        'name': 'Name',
        'industry': 'Industry',
        'your_quantity': 'Your Quantity',
        'current_price': 'Current Price',
        'your_value': 'Your Value',
        'price_change': 'Price Change %',
        'price_source': 'Price Source',
        'total_positions': 'Total Positions',
        'cash_position': 'Cash Position',
        'live_price_coverage': 'Live Price Coverage',
        'refresh_prices': '🔄 Refresh Prices',
        'portfolio_info': 'Portfolio Info',
        'portfolio_description': 'This portfolio is shared among multiple users with different ownership percentages.',
        'price_info': 'Prices are fetched live from Yahoo Finance when possible.',
        'fetching_prices': 'Fetching latest stock prices...',
        'fetching_price_for': 'Fetching price for {}...',
        'portfolio_app': 'Portfolio Overview Application',
        'data_disclaimer': 'Data provided by Yahoo Finance • Prices may be delayed',
        
        # Industries
        'Europe': 'Europe',
        'Oil & Gas': 'Oil & Gas',
        'Bank': 'Bank',
        'Chemicals': 'Chemicals',
        'Materials': 'Materials',
        'Automotive': 'Automotive',
        'European Banks': 'European Banks',
        'Worldwide': 'Worldwide',
        'DAX': 'DAX',
        'Software': 'Software',
        'United States': 'United States',
        'Airlines': 'Airlines',
        'Cash': 'Cash',
        'Other': 'Other',
        'N/A': 'N/A'
    },
    'de': {
        # Auth
        'portfolio_login': '🏦 Portfolio Anmeldung',
        'please_log_in': 'Bitte melden Sie sich an, um Ihr Portfolio zu sehen',
        'username': 'Benutzername',
        'password': 'Passwort',
        'enter_username': 'Benutzername eingeben',
        'enter_password': 'Passwort eingeben',
        'login': 'Anmelden',
        'login_successful': 'Anmeldung erfolgreich!',
        'invalid_credentials': 'Ungültiger Benutzername oder Passwort',
        'enter_both': 'Bitte geben Sie sowohl Benutzername als auch Passwort ein',
        'welcome': 'Willkommen, {}!',
        'portfolio_share': 'Portfolio-Anteil',
        'logout': 'Abmelden',
        
        # Dashboard
        'portfolio_overview': '📊 Portfolio-Übersicht - {}',
        'price_fetch_status': '⚠️ Preis-Abruf Status',
        'could_not_fetch': 'Konnten Live-Preise für {} Symbole nicht abrufen. Verwende Standardpreise:',
        'your_portfolio_value': 'Ihr Portfolio-Wert',
        'total_return': 'Gesamtrendite',
        'daily_change': 'Tagesänderung',
        'live_prices': 'Live-Preise',
        'daily_moves': 'Tägliche Positionsbewegungen',
        'period_1d': '1 Tag',
        'period_1w': '1 Woche',
        'period_1m': '1 Monat', 
        'period_1y': '1 Jahr',
        'position_returns': 'Positionsrenditen',
        'all_users_overview': 'Übersicht aller Benutzer-Portfolios',
        'user_portfolio_values': 'Portfolio-Werte nach Benutzer',
        'historical_performance': 'Historische Portfolio-Performance',
        'relative_performance': 'Relative Performance (Basis = 100)',
        'portfolio_vs_benchmark': 'Portfolio vs URTH Benchmark',
        'timeframe': 'Zeitraum',
        'granularity': 'Granularität',
        'daily': 'Täglich',
        'weekly': 'Wöchentlich',
        'monthly': 'Monatlich',
        'period_3m': '3 Monate',
        'period_6m': '6 Monate',
        'portfolio_allocation': 'Portfolio-Aufteilung',
        'holdings_distribution': 'Ihre Beteiligungsverteilung',
        'industry_breakdown': 'Branchen-Aufschlüsselung',
        'holdings_by_industry': 'Ihre Beteiligungen nach Branchen',
        'detailed_holdings': 'Detaillierte Beteiligungen',
        'symbol': 'Symbol',
        'name': 'Name',
        'industry': 'Branche',
        'your_quantity': 'Ihre Anzahl',
        'current_price': 'Aktueller Preis',
        'your_value': 'Ihr Wert',
        'price_change': 'Preisänderung %',
        'price_source': 'Preis-Quelle',
        'total_positions': 'Gesamtpositionen',
        'cash_position': 'Cash-Position',
        'live_price_coverage': 'Live-Preis Abdeckung',
        'refresh_prices': '🔄 Preise Aktualisieren',
        'portfolio_info': 'Portfolio-Info',
        'portfolio_description': 'Dieses Portfolio wird von mehreren Benutzern mit unterschiedlichen Eigentumsanteilen geteilt.',
        'price_info': 'Preise werden wenn möglich live von Yahoo Finance abgerufen.',
        'fetching_prices': 'Lade aktuelle Aktienkurse...',
        'fetching_price_for': 'Lade Preis für {}...',
        'portfolio_app': 'Portfolio-Übersicht Anwendung',
        'data_disclaimer': 'Daten von Yahoo Finance bereitgestellt • Preise können verzögert sein',
        
        # Industries
        'Europe': 'Europa',
        'Oil & Gas': 'Öl & Gas',
        'Bank': 'Bank',
        'Chemicals': 'Chemie',
        'Materials': 'Materialien',
        'Automotive': 'Automobil',
        'European Banks': 'Europäische Banken',
        'Worldwide': 'Weltweit',
        'DAX': 'DAX',
        'Software': 'Software',
        'United States': 'Vereinigte Staaten',
        'Airlines': 'Fluggesellschaften',
        'Cash': 'Bargeld',
        'Other': 'Andere',
        'N/A': 'N/V'
    }
}

def get_text(key: str, language: str = 'en', *args) -> str:
    """Get translated text for the given key and language"""
    text = TRANSLATIONS.get(language, TRANSLATIONS['en']).get(key, key)
    if args:
        return text.format(*args)
    return text

def format_currency(amount: float, language: str = 'en') -> str:
    """Format currency amount based on language"""
    currency_symbol = '€'
    return f"{currency_symbol}{amount:,.2f}"

def format_currency_change(amount: float, language: str = 'en') -> str:
    """Format currency change amount with proper sign and symbol"""
    currency_symbol = '€'
    return f"{currency_symbol}{amount:+,.2f}"

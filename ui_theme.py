"""A restrained visual theme for the portfolio dashboard."""

from html import escape


def build_app_css() -> str:
    """Return the global Streamlit CSS without touching milestone banners."""
    return r"""
:root {
    --app-bg: #f4f5f2;
    --panel-bg: rgba(255, 255, 255, 0.92);
    --panel-solid: #ffffff;
    --panel-soft: #eef3ef;
    --border: #dde2dc;
    --border-strong: #c9d0c8;
    --muted: #68736b;
    --text: #171c18;
    --accent: #176b4d;
    --accent-hover: #0f593e;
    --accent-soft: #dcece4;
    --gold: #a6782d;
    --positive: #087443;
    --negative: #bc3d42;
    --shadow: 0 12px 34px rgba(24, 38, 29, 0.065);
}

html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: var(--text);
    font-feature-settings: "cv02", "cv03", "cv04", "cv11";
}

.stApp,
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 8% -10%, rgba(23, 107, 77, 0.07), transparent 29rem),
        linear-gradient(180deg, #f8f9f7 0%, var(--app-bg) 34rem);
}

/* Remove vendor chrome while retaining the sidebar open/close control. */
#MainMenu,
footer,
[data-testid="stStatusWidget"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
.viewerBadge_container__1QSob {
    visibility: hidden;
    display: none;
}

[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1380px;
    padding-top: 2.7rem;
    padding-bottom: 4.5rem;
}

[data-testid="stSidebar"] {
    background: rgba(250, 251, 249, 0.97);
    border-right: 1px solid var(--border);
    box-shadow: 14px 0 40px rgba(24, 38, 29, 0.035);
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label {
    color: var(--muted);
    line-height: 1.5;
}

[data-testid="stSidebar"] h3 {
    color: var(--text);
    font-size: 0.78rem;
    font-weight: 750;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

h1, h2, h3 {
    color: var(--text);
    letter-spacing: -0.025em;
}

h1 { font-size: clamp(2rem, 3vw, 2.85rem); }
h2 { font-size: clamp(1.35rem, 2vw, 1.75rem); margin-top: 2.5rem; }
h3 { font-size: 1.08rem; margin-top: 1.75rem; }

p, label, .stCaption { color: var(--muted); }

hr {
    margin: 2.2rem 0;
    border: 0;
    border-top: 1px solid rgba(201, 208, 200, 0.62);
}

.portfolio-hero {
    position: relative;
    overflow: hidden;
    margin: 0 0 1.35rem;
    padding: clamp(1.5rem, 3vw, 2.5rem);
    border: 1px solid rgba(23, 107, 77, 0.19);
    border-radius: 24px;
    background:
        radial-gradient(circle at 92% 5%, rgba(166, 120, 45, 0.15), transparent 18rem),
        linear-gradient(135deg, #11251d 0%, #173c2d 52%, #22523f 100%);
    box-shadow: 0 18px 48px rgba(17, 37, 29, 0.15);
}

.portfolio-hero::after {
    content: "";
    position: absolute;
    right: -3rem;
    bottom: -6rem;
    width: 19rem;
    height: 19rem;
    border: 1px solid rgba(255,255,255,.12);
    border-radius: 50%;
    box-shadow: 0 0 0 3rem rgba(255,255,255,.035), 0 0 0 6rem rgba(255,255,255,.025);
}

.portfolio-hero__top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1.35rem;
}

.portfolio-hero__eyebrow {
    color: #b9d8c8;
    font-size: .72rem;
    font-weight: 800;
    letter-spacing: .18em;
}

.portfolio-hero__badge {
    padding: .35rem .7rem;
    border: 1px solid rgba(255,255,255,.2);
    border-radius: 999px;
    color: rgba(255,255,255,.78);
    background: rgba(255,255,255,.07);
    font-size: .69rem;
    font-weight: 700;
    letter-spacing: .08em;
}

.portfolio-hero h1 {
    position: relative;
    z-index: 1;
    margin: 0 !important;
    color: #fff !important;
    font-size: clamp(2.1rem, 5vw, 4rem) !important;
    font-weight: 520 !important;
    letter-spacing: -.045em !important;
    line-height: 1.02 !important;
}

.portfolio-hero h1 span { color: #cce7d8; }

.portfolio-hero p {
    position: relative;
    z-index: 1;
    max-width: 650px;
    margin: .85rem 0 0 !important;
    color: rgba(255,255,255,.7) !important;
    font-size: .98rem;
    line-height: 1.55;
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: .9rem;
    margin: .9rem 0 1.65rem;
}

.metric-card,
[data-testid="stMetric"] {
    position: relative;
    overflow: hidden;
    min-height: 118px;
    padding: 1.15rem 1.2rem;
    border: 1px solid rgba(201, 208, 200, .78);
    border-radius: 16px;
    background: var(--panel-bg);
    box-shadow: 0 8px 28px rgba(24, 38, 29, .045);
    transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
}

.metric-card:hover,
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    border-color: var(--border-strong);
    box-shadow: var(--shadow);
}

.metric-label,
[data-testid="stMetricLabel"] {
    color: var(--muted) !important;
    font-size: .73rem !important;
    font-weight: 720 !important;
    letter-spacing: .075em;
    line-height: 1.3;
    text-transform: uppercase;
}

.metric-value,
[data-testid="stMetricValue"] {
    margin-top: .62rem;
    color: var(--text) !important;
    font-size: clamp(1.35rem, 2.4vw, 1.85rem) !important;
    font-weight: 650 !important;
    letter-spacing: -.035em;
    line-height: 1.1;
    overflow-wrap: anywhere;
}

.metric-delta,
[data-testid="stMetricDelta"] {
    margin-top: .5rem;
    font-size: .84rem !important;
    font-weight: 700 !important;
}
.metric-delta.positive { color: var(--positive); }
.metric-delta.negative { color: var(--negative); }
.metric-delta.neutral { color: var(--muted); }

[data-testid="stPlotlyChart"],
[data-testid="stDataFrame"] {
    overflow: hidden;
    padding: .75rem;
    border: 1px solid rgba(201, 208, 200, .72);
    border-radius: 18px;
    background: var(--panel-solid);
    box-shadow: 0 8px 28px rgba(24, 38, 29, .04);
}

[data-testid="stForm"],
[data-testid="stExpander"] {
    border: 1px solid rgba(201, 208, 200, .82);
    border-radius: 16px;
    background: rgba(255,255,255,.82);
    box-shadow: 0 8px 28px rgba(24, 38, 29, .035);
}

[data-testid="stForm"] { padding: 1.2rem; }

.stTextInput input,
.stSelectbox [data-baseweb="select"] > div {
    min-height: 46px;
    border-color: var(--border-strong) !important;
    border-radius: 11px !important;
    background: #fff !important;
    box-shadow: none !important;
}

.stTextInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(23, 107, 77, .11) !important;
}

.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    min-height: 42px;
    padding: .55rem 1rem;
    border: 1px solid var(--border-strong);
    border-radius: 999px;
    color: var(--text);
    background: var(--panel-solid);
    font-weight: 680;
    transition: transform .16s ease, background .16s ease, border-color .16s ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {
    transform: translateY(-1px);
    border-color: var(--accent);
    color: var(--accent);
    background: #f7fbf8;
}

.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"],
.stFormSubmitButton > button {
    border-color: var(--accent) !important;
    color: #fff !important;
    background: var(--accent) !important;
}

.stFormSubmitButton > button:hover {
    border-color: var(--accent-hover) !important;
    color: #fff !important;
    background: var(--accent-hover) !important;
}

.stFormSubmitButton > button p { color: inherit; }

[data-baseweb="tab-list"] {
    gap: .35rem;
    padding: .3rem;
    border-radius: 999px;
    background: #e9ede9;
}

[data-baseweb="tab"] {
    height: 38px;
    padding: 0 .95rem;
    border-radius: 999px;
}

[data-baseweb="tab"][aria-selected="true"] {
    color: var(--text);
    background: #fff;
    box-shadow: 0 2px 8px rgba(24,38,29,.08);
}

[data-testid="stAlert"] {
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
}

.portfolio-footer {
    margin-top: 3.5rem;
    padding-top: 1.25rem;
    border-top: 1px solid var(--border);
    color: var(--muted);
    font-size: .75rem;
    letter-spacing: .02em;
    text-align: center;
}

.portfolio-footer strong { color: #49534c; font-weight: 700; }

.login-intro {
    max-width: 560px;
    margin: 1rem auto 1.4rem;
    text-align: center;
}
.login-intro h1 { margin: 0 !important; font-size: 2.15rem !important; }

@media (prefers-reduced-motion: reduce) {
    .metric-card, [data-testid="stMetric"], .stButton > button { transition: none; }
}

@media (max-width: 760px) {
    .block-container { padding: 1.5rem .85rem 3rem; }
    .portfolio-hero { padding: 1.4rem 1.2rem 1.55rem; border-radius: 18px; }
    .portfolio-hero__badge { display: none; }
    .portfolio-hero h1 { font-size: 2.25rem !important; }
    .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .65rem; }
    .metric-card { min-height: 105px; padding: .95rem; }
    .metric-value { font-size: 1.25rem !important; }
    [data-baseweb="tab-list"] { overflow-x: auto; justify-content: flex-start; }
}

@media (max-width: 430px) {
    .metric-grid { grid-template-columns: 1fr; }
    .portfolio-hero__top { margin-bottom: 1rem; }
}
"""


def build_dashboard_header(username: str, lang: str = "en") -> str:
    """Build a branded portfolio heading that replaces Streamlit's default title."""
    display_name = escape(username.strip().title())
    if lang == "de":
        subtitle = "Wertentwicklung, Allokation und Positionen auf einen Blick."
        badge = "ÜBERSICHT"
    else:
        subtitle = "Value, performance and allocation in one clear view."
        badge = "OVERVIEW"
    return f"""
<div class="portfolio-hero">
    <div class="portfolio-hero__top">
        <span class="portfolio-hero__eyebrow">PRIVATE PORTFOLIO</span>
        <span class="portfolio-hero__badge">{badge}</span>
    </div>
    <h1><span>{display_name}</span> Portfolio</h1>
    <p>{subtitle}</p>
</div>
"""


def build_footer(lang: str = "en") -> str:
    """Build a quiet footer without generic app branding."""
    if lang == "de":
        title = "Privates Portfolio"
        disclaimer = "Kursdaten von Yahoo Finance · Kurse können verzögert sein"
    else:
        title = "Private Portfolio"
        disclaimer = "Market data from Yahoo Finance · Quotes may be delayed"
    return f'<div class="portfolio-footer"><strong>{title}</strong><br>{disclaimer}</div>'


def build_login_intro(lang: str = "en") -> str:
    """Build the compact branded login introduction."""
    if lang == "de":
        title = "Portfolio Login"
    else:
        title = "Portfolio Login"
    return f"""
<div class="login-intro">
    <h1>{title}</h1>
</div>
"""

"""Milestone celebration rules and copy for the portfolio dashboard."""


def should_show_doubling_celebration(username: str, return_percentage: float) -> bool:
    """Return whether the Kremer account is inside the 100–105% milestone window."""
    try:
        value = float(return_percentage)
    except (TypeError, ValueError):
        return False
    return username == "kremer" and 100.0 <= value <= 105.0


def resolve_doubling_celebration_return(
    username: str,
    return_percentage: float,
    preview_requested: bool = False,
) -> float | None:
    """Return the percentage to celebrate, including Kremer's manual replay preview."""
    if username != "kremer":
        return None
    if preview_requested:
        return 102.4
    if should_show_doubling_celebration(username, return_percentage):
        return float(return_percentage)
    return None


def build_doubling_message(return_percentage: float) -> str:
    """Build the German milestone message using a German decimal separator."""
    formatted_return = f"{float(return_percentage):.1f}".replace(".", ",")
    return (
        "Herzlichen Glückwunsch! Ihr habt euer eingesetztes Geld verdoppelt! "
        f"Aktuelle Gesamtrendite: {formatted_return} %."
    )


def build_doubling_celebration_html(return_percentage: float) -> str:
    """Build a self-contained, animated milestone banner for Streamlit."""
    formatted_return = f"{float(return_percentage):.1f}".replace(".", ",")
    colors = ("#ffd166", "#ff5d8f", "#54e1ff", "#8cff98", "#b794f4", "#ffffff")
    shapes = []
    for index in range(52):
        left = (index * 37 + 11) % 100
        delay = -((index * 17) % 40) / 10
        duration = 3.6 + ((index * 13) % 22) / 10
        rotation = (index * 47) % 360
        color = colors[index % len(colors)]
        shape = "50%" if index % 4 == 0 else "2px"
        shapes.append(
            f'<i style="--x:{left}%;--delay:{delay}s;--duration:{duration}s;'
            f'--rotation:{rotation}deg;--color:{color};--radius:{shape}"></i>'
        )

    return f"""
<style>
.celebration-stage {{
    position: relative;
    isolation: isolate;
    overflow: hidden;
    margin: 1.1rem 0 1.6rem;
    padding: 2.25rem 1.5rem 2rem;
    border: 2px solid rgba(255, 209, 102, .9);
    border-radius: 22px;
    text-align: center;
    color: #fff;
    background:
        radial-gradient(circle at 18% 18%, rgba(255, 93, 143, .36), transparent 29%),
        radial-gradient(circle at 84% 12%, rgba(84, 225, 255, .32), transparent 27%),
        radial-gradient(circle at 50% 120%, rgba(255, 209, 102, .24), transparent 45%),
        linear-gradient(135deg, #17122f 0%, #32165d 48%, #101d46 100%);
    box-shadow: 0 20px 55px rgba(49, 22, 93, .35), inset 0 0 45px rgba(255,255,255,.05);
}}
.celebration-stage::before {{
    content: "";
    position: absolute;
    inset: 0;
    z-index: -1;
    opacity: .55;
    background-image:
        radial-gradient(circle, #fff 0 1px, transparent 1.7px),
        radial-gradient(circle, #ffd166 0 1.2px, transparent 2px);
    background-position: 0 0, 23px 31px;
    background-size: 47px 47px, 59px 59px;
    animation: celebration-twinkle 2.4s ease-in-out infinite alternate;
}}
.celebration-kicker {{
    display: inline-block;
    padding: .38rem .85rem;
    border: 1px solid rgba(255,255,255,.55);
    border-radius: 999px;
    color: #fff4bf;
    background: rgba(255,255,255,.1);
    font-size: .78rem;
    font-weight: 800;
    letter-spacing: .16em;
    text-transform: uppercase;
}}
.celebration-trophy {{
    display: block;
    margin: .65rem auto .15rem;
    font-size: 4rem;
    line-height: 1;
    filter: drop-shadow(0 8px 15px rgba(0,0,0,.28));
    animation: celebration-trophy 1.4s ease-in-out infinite alternate;
}}
.celebration-stage h2 {{
    margin: .35rem 0 .55rem !important;
    color: #fff !important;
    font-size: clamp(1.75rem, 5vw, 3.25rem) !important;
    font-weight: 900 !important;
    letter-spacing: .035em !important;
    text-shadow: 0 3px 0 rgba(0,0,0,.2), 0 0 24px rgba(255,209,102,.35);
}}
.celebration-stage p {{
    max-width: 720px;
    margin: 0 auto !important;
    color: rgba(255,255,255,.92) !important;
    font-size: 1.05rem;
}}
.celebration-return {{
    display: inline-block;
    margin-top: 1rem;
    padding: .6rem 1rem;
    border-radius: 12px;
    color: #251841;
    background: linear-gradient(135deg, #fff4bf, #ffd166);
    box-shadow: 0 8px 24px rgba(255,209,102,.25);
    font-size: 1.25rem;
    font-weight: 900;
}}
.celebration-side {{
    position: absolute;
    top: 44%;
    z-index: 1;
    font-size: 2rem;
    animation: celebration-pop 1.2s ease-in-out infinite alternate;
}}
.celebration-side.left {{ left: 7%; }}
.celebration-side.right {{ right: 7%; animation-delay: -.6s; }}
.celebration-confetti {{
    position: absolute;
    inset: 0;
    z-index: 2;
    overflow: hidden;
    pointer-events: none;
}}
.celebration-confetti i {{
    position: absolute;
    top: -18px;
    left: var(--x);
    width: 8px;
    height: 15px;
    border-radius: var(--radius);
    background: var(--color);
    opacity: .9;
    transform: rotate(var(--rotation));
    animation: celebration-fall var(--duration) linear var(--delay) infinite;
}}
@keyframes celebration-fall {{
    0% {{ transform: translate3d(0,-18px,0) rotate(var(--rotation)); }}
    50% {{ transform: translate3d(18px,190px,0) rotate(calc(var(--rotation) + 280deg)); }}
    100% {{ transform: translate3d(-12px,430px,0) rotate(calc(var(--rotation) + 620deg)); }}
}}
@keyframes celebration-twinkle {{ from {{ opacity: .3; }} to {{ opacity: .72; }} }}
@keyframes celebration-trophy {{ from {{ transform: rotate(-4deg) scale(1); }} to {{ transform: rotate(4deg) scale(1.09); }} }}
@keyframes celebration-pop {{ from {{ transform: scale(.86) rotate(-8deg); }} to {{ transform: scale(1.14) rotate(8deg); }} }}
@media (prefers-reduced-motion: reduce) {{
    .celebration-stage::before, .celebration-trophy, .celebration-side, .celebration-confetti i {{ animation: none !important; }}
    .celebration-confetti i {{ top: calc((var(--x) * .035) + 8px); }}
}}
@media (max-width: 600px) {{
    .celebration-stage {{ padding: 1.8rem .9rem 1.6rem; border-radius: 17px; }}
    .celebration-trophy {{ font-size: 3.25rem; }}
    .celebration-side {{ display: none; }}
}}
</style>
<div class="celebration-stage" role="status" aria-label="Das Kremer-Depot hat sein eingesetztes Kapital verdoppelt.">
    <div class="celebration-confetti" aria-hidden="true">{"".join(shapes)}</div>
    <span class="celebration-side left" aria-hidden="true">🎆</span>
    <span class="celebration-side right" aria-hidden="true">🎇</span>
    <div class="celebration-kicker">100 % GEKNACKT</div>
    <span class="celebration-trophy" aria-hidden="true">🏆</span>
    <h2>DOPPELT HÄLT BESSER!</h2>
    <p>Herzlichen Glückwunsch! Ihr habt euer eingesetztes Geld verdoppelt.</p>
    <div class="celebration-return">🚀 Gesamtrendite: {formatted_return} %</div>
</div>
"""

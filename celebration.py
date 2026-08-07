"""Milestone celebration rules and copy for the portfolio dashboard."""


def should_show_doubling_celebration(username: str, return_percentage: float) -> bool:
    """Return whether the Kremer account is inside the 100–105% milestone window."""
    try:
        value = float(return_percentage)
    except (TypeError, ValueError):
        return False
    return username == "kremer" and 100.0 <= value <= 105.0


def build_doubling_message(return_percentage: float) -> str:
    """Build the German milestone message using a German decimal separator."""
    formatted_return = f"{float(return_percentage):.1f}".replace(".", ",")
    return (
        "Herzlichen Glückwunsch! Ihr habt euer eingesetztes Geld verdoppelt! "
        f"Aktuelle Gesamtrendite: {formatted_return} %."
    )

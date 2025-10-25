from django import template

register = template.Library()


@register.filter(name="two_dec")
def two_dec(value):
    """Format a numeric value with two decimal places (e.g., 0.00).

    Safely handles None, strings, Decimal, and other numeric-like inputs.
    Returns a string.
    """
    try:
        # Treat None and empty strings as 0
        if value is None or value == "":
            num = 0.0
        else:
            num = float(value)
        return f"{num:.2f}"
    except Exception:
        # As a last resort, return 0.00
        return "0.00"

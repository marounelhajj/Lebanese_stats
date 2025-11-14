# stats/templatetags/custom_filters.py
from django import template

register = template.Library()


@register.filter
def mul100(value):
    """
    Multiply numeric value by 100. Safely handles empty / bad values.
    """
    try:
        return float(value) * 100.0
    except (TypeError, ValueError):
        return 0.0

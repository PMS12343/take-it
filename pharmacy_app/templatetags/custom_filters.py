from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiply the given value by the argument."""
    try:
        result = Decimal(str(value)) * Decimal(str(arg))
        return result
    except (ValueError, TypeError):
        return 0


from django import template

register = template.Library()

@register.filter
def sum(values):
    return sum(values)
    
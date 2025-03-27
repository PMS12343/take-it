from django import template

register = template.Library()

@register.filter
def sum_values(values):
    """Custom filter to sum a list of values.
    This is required because the name 'sum' would conflict with Python's built-in sum function.
    
    Example usage in templates:
    {{ my_list|sum_values }}
    """
    if not values:
        return 0
    return sum(values)

@register.filter
def sum(values, key=None):
    """Sum a property from each item in a list of dictionaries.
    
    Example usage in templates:
    {{ list_of_dicts|sum:"property_name" }}
    """
    if not values:
        return 0
    
    if key:
        # Sum the specified property from each dictionary in the list
        total = 0
        for d in values:
            try:
                total += float(d.get(key, 0))
            except (TypeError, ValueError):
                pass
        return total
    else:
        # If no key is provided, attempt to sum the values directly
        total = 0
        for v in values:
            try:
                total += float(v)
            except (TypeError, ValueError):
                pass
        return total
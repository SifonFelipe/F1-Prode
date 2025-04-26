from django import template

register = template.Library()

@register.filter
def clean_float(value):
    try:
        value = float(value)
        if value.is_integer():
            return int(value)
        return round(value, 2)
    except:
        return value
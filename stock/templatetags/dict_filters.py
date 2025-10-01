from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def sum_list(value):

    try:
        return sum(value)
    except Exception:
        return 0
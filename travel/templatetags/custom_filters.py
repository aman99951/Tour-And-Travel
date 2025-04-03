from django import template
from django.utils.html import strip_tags

register = template.Library()


@register.filter
def preserve_formatting(value):
    """
    This filter ensures the HTML content is not stripped and preserves 
    rich text formatting such as lists, paragraphs, and other HTML tags.
    """
    return value

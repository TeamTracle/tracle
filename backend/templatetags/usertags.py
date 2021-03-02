import re

from django.template import Library
from django.utils.html import format_html


register = Library()

@register.filter
def usertags(text):
    pattern = re.compile('\@\((.+)\)\[(.*)\]')
    return re.sub(pattern, '@\\1', text)
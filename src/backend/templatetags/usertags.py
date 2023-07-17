import re

from django.template import Library


register = Library()


@register.filter
def usertags(text):
    pattern = re.compile("\@\((.+)\)\[(.*)\]")  # noqa: W605
    return re.sub(pattern, "@\\1", text)

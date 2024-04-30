from django.contrib.admin.templatetags.admin_list import search_form
from django.template import Library

register = Library()

register.inclusion_tag(
    "barcodes/search_form.html",
    takes_context=False,
    name="barcodes_search_form",
)(search_form)

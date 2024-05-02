from django import template
from django.contrib.admin.templatetags.admin_modify import submit_row

from ..apps import AdminButtonsConfig

register = template.Library()

register.inclusion_tag(
    f"{AdminButtonsConfig.name}/submit_line.html",
    takes_context=True,
    name="custom_submit_row",
)(submit_row)

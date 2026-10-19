import logging

import six
from django.conf import settings
from django.template import Template
from wagov_utils.components.utils.email import (
    TemplateEmailBase as WAGovUtilsTemplateEmailBase,
)

logger = logging.getLogger(__name__)


def _render(template, context):
    if isinstance(context, dict):
        context.update({"settings": settings})
    if isinstance(template, six.string_types):
        template = Template(template)
    return template.render(context)


class TemplateEmailBase(WAGovUtilsTemplateEmailBase):
    subject = ""
    html_template = "boranga/emails/base_email.html"
    # txt_template can be None, in this case a 'tag-stripped' version of the html will be sent. (see send)
    txt_template = "boranga/emails/base-email.txt"

    def send_to_user(self, users, context=None):
        filtered_emails = {u.email for u in users if hasattr(u, "email")}
        # Loop through users
        for email in filtered_emails:
            # Send the email!
            self.send(email, context=context)


class ExportReportEmail(TemplateEmailBase):
    def __init__(self, model_name=""):
        self.model_name = model_name

    model_name = ""
    subject = f"Attached: Apiary - {model_name.capitalize()} Report"
    html_template = "disturbance/emails/report_attached.html"
    txt_template = "disturbance/emails/report_attached.txt"

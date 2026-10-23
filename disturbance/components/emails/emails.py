import logging

from wagov_utils.components.utils.email import (
    TemplateEmailBase as WAGovUtilsTemplateEmailBase,
)

logger = logging.getLogger(__name__)


class TemplateEmailBase(WAGovUtilsTemplateEmailBase):
    subject = ""
    html_template = "disturbance/emails/apiary_base_email.html"
    # txt_template can be None, in this case a 'tag-stripped' version of the html will be sent. (see send)
    txt_template = "disturbance/emails/apiary_base_email.txt"

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


class CronNotificationEmail(TemplateEmailBase):
    subject = "Apiary - Cronjob"
    html_template = "disturbance/emails/base_cron.html"
    txt_template = "disturbance/emails/base_cron.txt"

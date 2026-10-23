import logging
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from disturbance.components.emails.emails import CronNotificationEmail

logger = logging.getLogger(__name__)

LOGFILE = "logs/cron_tasks.log"


class Command(BaseCommand):
    help = "Run the Disturbance Cron tasks"

    def handle(self, *args, **options):
        stdout_redirect = f" | tee -a {LOGFILE}"
        subprocess.call(f"cat /dev/null > {LOGFILE}", shell=True)  # empty the log file

        logger.info(f"Running command {__name__}")
        subprocess.call("python manage.py update_compliance_status" + stdout_redirect, shell=True)
        subprocess.call("python manage.py send_compliance_reminder" + stdout_redirect, shell=True)
        subprocess.call("python manage.py update_approval_status" + stdout_redirect, shell=True)
        subprocess.call("python manage.py expire_approvals" + stdout_redirect, shell=True)
        subprocess.call("python manage.py approval_renewal_notices" + stdout_redirect, shell=True)
        subprocess.call("python manage.py send_assessment_reminder" + stdout_redirect, shell=True)
        subprocess.call("python manage.py weekly_assessment_reminder" + stdout_redirect, shell=True)
        subprocess.call(
            "python manage.py send_annual_rental_fee_invoice" + stdout_redirect,
            shell=True,
        )
        subprocess.call("python manage.py save_apiary_sites" + stdout_redirect, shell=True)

        logger.info(f"Command {__name__} completed")
        self.send_email()

    def send_email(self):
        log_txt = Path(LOGFILE).read_text()
        to = (
            settings.CRON_NOTIFICATION_EMAIL
            if isinstance(settings.CRON_NOTIFICATION_EMAIL, list)
            else [settings.CRON_NOTIFICATION_EMAIL]
        )

        context = {
            "log_txt": log_txt,
        }

        email = CronNotificationEmail()
        email.send(to, context=context)

import logging

import django_cron
from django.core import management

from disturbance import settings

log = logging.getLogger(__name__)


class CronJobProcessReportQueue(django_cron.CronJobBase):
    """Process pending report export jobs from the JobQueue every 2 minutes."""

    schedule = django_cron.Schedule(run_weekly_on_days=[0, 1, 2, 3, 4, 5, 6], run_every_mins=2)
    code = "apiary.process_report_queue"

    def do(self) -> None:
        log.info("Process report queue cron job triggered, running...")
        management.call_command("run_queue_job")
        return "Job Completed Successfully"


class CronJobCronTasks(django_cron.CronJobBase):
    """Run the Apiary Cron tasks every 2 minutes."""

    schedule = django_cron.Schedule(run_weekly_on_days=[0, 1, 2, 3, 4, 5, 6], run_every_mins=2)
    code = "apiary.cron_tasks"

    def do(self) -> None:
        log.info("Cron tasks cron job triggered, running...")
        management.call_command("cron_tasks")
        return "Job Completed Successfully"


class CronJobPopulateOrganisationProperties(django_cron.CronJobBase):
    """Sync the local Organisation name and abn from ledger once per day in case details are changed."""

    schedule = django_cron.Schedule(
        run_weekly_on_days=[0, 1, 2, 3, 4, 5, 6], run_at_times=settings.POPULATE_ORGANISATION_PROPERTIES_RUN_AT_TIMES
    )
    code = "apiary.populate_organisation_properties"

    def do(self) -> None:
        log.info("Populate Organisation Properties Cron Job triggered, running...")
        management.call_command("populate_organisation_properties")
        return "Job Completed Successfully"

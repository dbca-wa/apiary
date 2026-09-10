import logging

from django.core.management import CommandError
from django.core.management.base import BaseCommand

from disturbance.components.organisations.models import Organisation

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            # Use all organisations as the name or abn could be changed in ledger
            for org in Organisation.objects.all():
                org.update_property_cache()
        except Exception as exc:
            logger.exception(
                "Unexpected error occurred while running populate_organisation_properties management command"
            )

            # 2. Crash the CLI gracefully with a clean exit code
            raise CommandError(f"Command failed: {exc}")

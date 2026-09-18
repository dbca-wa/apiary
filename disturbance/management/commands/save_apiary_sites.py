import json
import logging
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from disturbance.components.approvals.serializers_apiary import (
    ApiarySiteOnApprovalGeometryExportSerializer,
)
from disturbance.components.main.utils import (
    get_qs_approval_for_export,
    get_qs_proposal_for_export,
    get_qs_vacant_site_for_export,
)
from disturbance.components.proposals.serializers_apiary import (
    ApiarySiteOnProposalDraftGeometryExportSerializer,
    ApiarySiteOnProposalProcessedGeometryExportSerializer,
)

logger = logging.getLogger(__name__)


def serialize_records_safely(serializer_class, queryset, label=""):
    """
    Serializes records one by one so a single failing record:
    1. Does not abort the whole export.
    2. Logs the exact failing record ID and traceback.
    """
    features = []
    errors = []

    for item in queryset:
        try:
            # Single-instance serialization returns a single GeoJSON Feature
            data = serializer_class(item).data
            features.append(data)
        except Exception as e:
            item_id = getattr(item, "id", "Unknown")
            site_id = getattr(getattr(item, "apiary_site", None), "id", None)
            err_msg = f"[{label}] Failed to serialize Record ID {item_id} (Apiary Site ID: {site_id}): {e}"
            logger.error(err_msg, exc_info=True)
            errors.append(err_msg)

    return features, errors


class Command(BaseCommand):
    help = "Save the apiary sites as a GeoJSON file"

    def handle(self, *args, **options):
        cmd_name = self.__module__.split(".")[-1].replace("_", " ").upper()
        self.stdout.write(f"Starting {cmd_name}...")

        all_errors = []
        all_features = []

        try:
            # 1. Retrieve 'vacant' sites
            qs_vacant_proposal, qs_vacant_approval = get_qs_vacant_site_for_export()

            feat, errs = serialize_records_safely(
                ApiarySiteOnProposalDraftGeometryExportSerializer,
                qs_vacant_proposal.filter(wkb_geometry_processed__isnull=True),
                label="Vacant Proposal (Draft Geometry)",
            )
            all_features.extend(feat)
            all_errors.extend(errs)

            feat, errs = serialize_records_safely(
                ApiarySiteOnProposalProcessedGeometryExportSerializer,
                qs_vacant_proposal.filter(wkb_geometry_processed__isnull=False),
                label="Vacant Proposal (Processed Geometry)",
            )
            all_features.extend(feat)
            all_errors.extend(errs)

            feat, errs = serialize_records_safely(
                ApiarySiteOnApprovalGeometryExportSerializer,
                qs_vacant_approval,
                label="Vacant Approval",
            )
            all_features.extend(feat)
            all_errors.extend(errs)

            # 2. ApiarySiteOnProposal & ApiarySiteOnApproval
            _, qs_on_proposal_processed = get_qs_proposal_for_export()
            qs_on_approval = get_qs_approval_for_export()

            # Exclude duplicates
            qs_on_proposal_processed = qs_on_proposal_processed.exclude(
                apiary_site__in=qs_on_approval.values("apiary_site")
            )

            # 3. Serialize Proposal & Approval
            feat, errs = serialize_records_safely(
                ApiarySiteOnProposalProcessedGeometryExportSerializer,
                qs_on_proposal_processed,
                label="Proposal Processed",
            )
            all_features.extend(feat)
            all_errors.extend(errs)

            feat, errs = serialize_records_safely(
                ApiarySiteOnApprovalGeometryExportSerializer,
                qs_on_approval,
                label="Approval",
            )
            all_features.extend(feat)
            all_errors.extend(errs)

            # 4. Construct Final GeoJSON FeatureCollection
            export_data = {
                "type": "FeatureCollection",
                "features": all_features,
            }

            # 5. Save to file (Atomic write)
            save_dir = Path(settings.BASE_DIR) / settings.SPATIAL_DATA_DIR
            save_dir.mkdir(parents=True, exist_ok=True)

            timestamp = timezone.localtime(timezone.now()).strftime("%Y%m%d-%H%M%S")
            target_file = save_dir / f"{timestamp}-apiary-sites.json"
            temp_file = target_file.with_suffix(".tmp")

            with open(temp_file, "w") as fp:
                json.dump(export_data, fp)
            temp_file.replace(target_file)

            # 6. Rotate files (keep latest 3)
            existing_files = sorted(
                save_dir.glob("*-apiary-sites.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )
            for old_file in existing_files[3:]:
                try:
                    old_file.unlink()
                except OSError as e:
                    logger.warning(f"Could not remove old file {old_file}: {e}")

        except Exception as e:
            logger.exception(f"Critical failure in {cmd_name}")
            all_errors.append(f"Critical execution error: {str(e)}")

        # 7. Summary Reporting
        if all_errors:
            err_str = f'<strong style="color: red;">Errors: {len(all_errors)}</strong>'
            self.stderr.write(self.style.ERROR(f"Completed with {len(all_errors)} error(s):"))
            for err in all_errors:
                self.stderr.write(self.style.WARNING(f"  - {err}"))
        else:
            err_str = '<strong style="color: green;">Errors: 0</strong>'
            self.stdout.write(self.style.SUCCESS(f"Successfully exported {len(all_features)} sites with 0 errors."))

        msg = f"<p>{cmd_name} completed. {err_str}. ({len(all_features)} sites exported)</p>"
        logger.info(msg)

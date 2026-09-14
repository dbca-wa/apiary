import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.conf import settings
from django.utils import timezone
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from rest_framework import serializers

from disturbance.components.ap_payments.models import AnnualRentalFee, AnnualRentalFeePeriod
from disturbance.components.ap_payments.serializers import AnnualRentalFeePeriodSerializer, AnnualRentalFeeSerializer
from disturbance.components.approvals.models import (
    ApiarySiteOnApproval,
    Approval,
    ApprovalDocument,
    ApprovalLogEntry,
    ApprovalUserAction,
)
from disturbance.components.main.serializers import CommunicationLogEntrySerializer
from disturbance.components.main.utils import get_region_district, get_tenure
from disturbance.components.organisations.models import Organisation
from disturbance.components.proposals.models import ApiaryAnnualRentalFee, SiteCategory
from disturbance.components.proposals.serializers_apiary import (
    ApiaryProposalRequirementSerializer,
    ApplicantAddressSerializer,
    OrgAddressSerializer,
)

logger = logging.getLogger(__name__)


class EmailUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        fields = ("id", "email", "first_name", "last_name", "title", "organisation")


class ApprovalWrapperSerializer(serializers.ModelSerializer):
    class Meta:
        model = Approval
        fields = (
            "id",
            "apiary_approval",
        )


class ApprovalDocumentHistorySerializer(serializers.ModelSerializer):
    history_date = serializers.SerializerMethodField()
    history_document_url = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalDocument
        fields = (
            "history_date",
            "history_document_url",
        )

    def get_history_date(self, obj):
        date_format_loc = timezone.localtime(obj.uploaded_date)
        history_date = date_format_loc.strftime("%d/%m/%Y %H:%M:%S.%f")

        return history_date

    def get_history_document_url(self, obj):
        url = obj._file.url
        return url


def bulk_fetch_gis_data(relations, max_workers=20):
    """Fetches tenure and region/district for all site relations concurrently

    using a thread pool to avoid sequential HTTP request bottlenecks.
    """
    gis_map = {}

    def _fetch_single_site_gis(relation):
        geom = getattr(relation, "wkb_geometry", None)
        if not geom:
            return relation.id, "", ""

        tenure_val = ""
        region_val = ""

        # 1. Fetch Tenure
        try:
            tenure_val = get_tenure(geom) or ""
        except Exception as e:
            logger.warning(f"Failed to fetch tenure for relation {relation.id}: {e}")

        # 2. Fetch Region/District
        try:
            region_val = get_region_district(geom) or ""
        except Exception as e:
            logger.warning(f"Failed to fetch region/district for relation {relation.id}: {e}")

        return relation.id, tenure_val, region_val

    # Convert queryset/generator to list so we know count
    relations_list = list(relations)
    if not relations_list:
        return {}

    # Adjust workers to not exceed the number of items
    workers = min(max_workers, len(relations_list))

    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all fetch jobs to the pool
        futures = {executor.submit(_fetch_single_site_gis, rel): rel for rel in relations_list}

        for future in as_completed(futures):
            try:
                relation_id, tenure, region = future.result()
                gis_map[relation_id] = {
                    "tenure": tenure,
                    "region_district": region,
                }
            except Exception as e:
                rel = futures[future]
                logger.error(f"Unexpected error in bulk GIS worker for relation {rel.id}: {e}")
                gis_map[rel.id] = {"tenure": "", "region_district": ""}

    return gis_map


class ApprovalSerializerForLicenceDoc(serializers.ModelSerializer):
    authority_holder = serializers.SerializerMethodField()
    authority_holder_address = serializers.SerializerMethodField()
    trading_name = serializers.SerializerMethodField()
    authority_number = serializers.SerializerMethodField()
    licence_start_date = serializers.SerializerMethodField()
    licence_expiry_date = serializers.SerializerMethodField()
    issue_date = serializers.SerializerMethodField()
    approver = serializers.SerializerMethodField()
    apiary_sites = serializers.SerializerMethodField()
    apiary_licensed_sites = serializers.SerializerMethodField()
    requirements = serializers.SerializerMethodField()
    map_ref = serializers.SerializerMethodField()
    batch_no = serializers.SerializerMethodField()
    cpc_date = serializers.SerializerMethodField()
    minister_date = serializers.SerializerMethodField()
    forest_block = serializers.SerializerMethodField()
    cog = serializers.SerializerMethodField()
    roadtrack = serializers.SerializerMethodField()
    zone = serializers.SerializerMethodField()
    catchment = serializers.SerializerMethodField()
    dra_permit = serializers.SerializerMethodField()

    def _get_relations_data(self, approval):
        """Fetch all relations and build their data with ZERO per-row queries."""
        if hasattr(self, "_cached_relations_data"):
            return self._cached_relations_data

        # 1. Pre-calculate fees per category ONCE (2-3 queries total instead of 750+)
        category_cache = {}
        for cat in SiteCategory.objects.all():
            category_cache[cat.id] = {
                "display_name": cat.display_name,
                "name": cat.name,
                "fee_renewal": cat.fee_renewal_per_site,
                "fee_transfer": cat.fee_transfer_per_site,
            }

        # 2. Fetch rental fees ONCE (1 query)
        fees_applied = ApiaryAnnualRentalFee.get_fees_by_period(approval.start_date, approval.expiry_date)
        first_fee = fees_applied[0] if fees_applied else {}
        fee_south_west = first_fee.get("amount_south_west_per_year", 0)
        fee_remote = first_fee.get("amount_remote_per_year", 0)

        # 3. Fetch relations with pre-fetched foreign keys (1 query)
        relations = (
            ApiarySiteOnApproval.objects.filter(approval=approval)
            .exclude(site_status=settings.SITE_STATUS_TRANSFERRED)
            .select_related("apiary_site", "site_category")
            .order_by("apiary_site_id")
        )

        # 4. Fetch GIS in parallel
        gis_map = bulk_fetch_gis_data(relations)

        licensed_sites = []
        unlicensed_sites = []

        for rel in relations:
            cat_data = category_cache.get(rel.site_category_id, {})
            is_sw = cat_data.get("name") == SiteCategory.CATEGORY_SOUTH_WEST
            annual_fee = fee_south_west if is_sw else fee_remote

            gis_info = gis_map.get(rel.id, {"tenure": "", "region_district": ""})
            geom = rel.wkb_geometry

            site_dict = {
                "id": rel.apiary_site_id,
                "coords": ({"lng": geom.x, "lat": geom.y} if geom else {"lng": "", "lat": ""}),
                "site_category": cat_data.get("display_name", ""),
                "tenure": gis_info["tenure"],
                "region_district": gis_info["region_district"],
                "licensed_site": rel.licensed_site or False,
                "batch_no": getattr(rel, "batch_no", "") or "",
                "approval_cpc_date": (getattr(rel, "approval_cpc_date", "") or ""),
                "approval_minister_date": (getattr(rel, "approval_minister_date", "") or ""),
                "map_ref": getattr(rel, "map_ref", "") or "",
                "forest_block": getattr(rel, "forest_block", "") or "",
                "cog": getattr(rel, "cog", "") or "",
                "roadtrack": getattr(rel, "roadtrack", "") or "",
                "zone": getattr(rel, "zone", "") or "",
                "catchment": getattr(rel, "catchment", "") or "",
                "dra_permit": ("Yes" if getattr(rel, "dra_permit", False) else "No"),
                "fee_application": annual_fee,
                "fee_renewal": cat_data.get("fee_renewal", 0),
                "fee_transfer": cat_data.get("fee_transfer", 0),
            }

            if rel.licensed_site:
                licensed_sites.append(site_dict)
            else:
                unlicensed_sites.append(site_dict)

        self._cached_relations_data = (unlicensed_sites, licensed_sites)
        return self._cached_relations_data

    def get_apiary_sites(self, approval):
        unlicensed_sites, _ = self._get_relations_data(approval)
        return unlicensed_sites

    def get_apiary_licensed_sites(self, approval):
        _, licensed_sites = self._get_relations_data(approval)
        return licensed_sites

    def get_requirements(self, approval):
        return [{"id": req.id, "text": req.requirement} for req in approval.proposalrequirement_set.all()]

    def get_authority_holder(self, approval):
        return approval.relevant_applicant_name

    def get_authority_holder_address(self, approval):
        return ", ".join(approval.relevant_applicant_address.values())

    def get_trading_name(self, approval):
        # return approval.applicant.trading_name if approval.applicant else ''
        try:
            return approval.applicant.trading_name if approval.applicant.trading_name else ""
        except:
            return ""

    def get_authority_number(self, approval):
        return approval.lodgement_number

    def get_licence_start_date(self, approval):
        return approval.start_date.strftime("%d %B %Y")

    def get_licence_expiry_date(self, approval):
        return approval.expiry_date.strftime("%d %B %Y")

    def get_issue_date(self, approval):
        return approval.issue_date.strftime("%d/%m/%Y")

    def get_approver(self, approval):

        approver = EmailUser.objects.filter(id=approval.approver_id).first() if approval.approver_id else None

        return approver.get_full_name() if approver else ""

    def get_map_ref(self, approval):
        return ""

    def get_forest_block(self, approval):
        return ""

    def get_cog(self, approval):
        return ""

    def get_roadtrack(self, approval):
        return ""

    def get_zone(self, approval):
        return ""

    def get_catchment(self, approval):
        return ""

    def get_dra_permit(self, approval):
        return "No"

    def get_batch_no(self, approval):
        return ""

    def get_cpc_date(self, approval):
        return ""

    def get_minister_date(self, approval):
        return ""

    class Meta:
        model = Approval
        fields = (
            "id",
            "authority_holder",
            "authority_holder_address",
            "trading_name",
            "authority_number",
            "licence_start_date",
            "licence_expiry_date",
            "issue_date",
            "approver",
            "apiary_sites",
            "apiary_licensed_sites",
            "requirements",
            "map_ref",
            "batch_no",
            "cpc_date",
            "minister_date",
            "forest_block",
            "cog",
            "roadtrack",
            "zone",
            "catchment",
            "dra_permit",
        )


class ApprovalSerializer(serializers.ModelSerializer):
    applicant = serializers.SerializerMethodField(read_only=True)
    applicant_id = serializers.SerializerMethodField(read_only=True)
    licence_document = serializers.CharField(source="licence_document._file.url")

    renewal_document = serializers.SerializerMethodField(read_only=True)
    status = serializers.CharField(source="get_status_display")
    allowed_assessors = EmailUserSerializer(many=True)
    region = serializers.CharField(source="current_proposal.region.name", allow_null=True)
    district = serializers.CharField(source="current_proposal.district.name", allow_null=True)

    activity = serializers.SerializerMethodField(read_only=True)
    title = serializers.CharField(source="current_proposal.title")

    can_approver_reissue = serializers.SerializerMethodField(read_only=True)
    application_type = serializers.SerializerMethodField(read_only=True)

    organisation = serializers.SerializerMethodField()
    applicant_first_name = serializers.SerializerMethodField()
    applicant_last_name = serializers.SerializerMethodField()
    applicant_address = serializers.SerializerMethodField()

    annual_rental_fee_periods = serializers.SerializerMethodField()
    latest_apiary_licence_document = serializers.SerializerMethodField()
    apiary_licence_document_history = serializers.SerializerMethodField()
    requirements = serializers.SerializerMethodField()
    template_group = serializers.SerializerMethodField()

    class Meta:
        model = Approval
        fields = (
            "id",
            "lodgement_number",
            "migrated",
            "licence_document",
            "replaced_by",
            "current_proposal_id",
            "activity",
            "region",
            "district",
            "tenure",
            "title",
            "renewal_document",
            "renewal_sent",
            "issue_date",
            "original_issue_date",
            "start_date",
            "expiry_date",
            "surrender_details",
            "suspension_details",
            "applicant",
            "applicant_id",
            "extracted_fields",
            "status",
            "reference",
            "can_reissue",
            "allowed_assessors",
            "cancellation_date",
            "cancellation_details",
            "applicant_id",
            "can_action",
            "set_to_cancel",
            "set_to_surrender",
            "set_to_suspend",
            "can_renew",
            "can_amend",
            "can_reinstate",
            "can_approver_reissue",
            "application_type",
            "current_proposal",
            "apiary_approval",
            "organisation",
            "applicant_first_name",
            "applicant_last_name",
            "applicant_address",
            "annual_rental_fee_periods",
            "no_annual_rental_fee_until",
            "latest_apiary_licence_document",
            "apiary_licence_document_history",
            "no_annual_rental_fee_until",
            "requirements",
            "template_group",
        )
        # the serverSide functionality of datatables is such that only columns that have field 'data' defined are requested from the serializer. We
        # also require the following additional fields for some of the mRender functions
        datatables_always_serialize = (
            "id",
            "migrated",
            "activity",
            "region",
            "title",
            "status",
            "reference",
            "lodgement_number",
            "licence_document",
            "start_date",
            "expiry_date",
            "applicant",
            "can_reissue",
            "can_action",
            "can_reinstate",
            "can_amend",
            "can_renew",
            "set_to_cancel",
            "set_to_suspend",
            "set_to_surrender",
            "current_proposal_id",
            "renewal_document",
            "renewal_sent",
            "allowed_assessors",
            "can_approver_reissue",
            "apiary_approval",
            "latest_apiary_licence_document",
            "template_group",
        )

    def get_activity(self, approval):
        activity_text = None
        if approval.apiary_approval:
            activity_text = "Apiary"
        else:
            activity_text = approval.current_proposal.activity
        return activity_text

    def get_requirements(self, approval):
        requirements = []
        for proposal in approval.proposal_set.all():
            for requirement in proposal.requirements.all():
                requirements.append(ApiaryProposalRequirementSerializer(requirement).data)
        return requirements

    def get_annual_rental_fee_periods(self, approval):
        annual_rental_fee_periods_qs = (
            AnnualRentalFeePeriod.objects.filter(
                annual_rental_fees__in=AnnualRentalFee.objects.filter(approval=approval)
            )
            .distinct()
            .order_by("period_start_date")
        )

        retrun_obj = []
        for annual_rental_fee_period in annual_rental_fee_periods_qs:
            serializer1 = AnnualRentalFeePeriodSerializer(annual_rental_fee_period)
            temp = serializer1.data
            temp["annual_rental_fees"] = []

            annual_rental_fee_qs = AnnualRentalFee.objects.filter(
                approval=approval, annual_rental_fee_period=annual_rental_fee_period
            )
            for annual_rental_fee in annual_rental_fee_qs:
                serializer2 = AnnualRentalFeeSerializer(annual_rental_fee)
                temp["annual_rental_fees"].append(serializer2.data)

            retrun_obj.append(temp)

        return retrun_obj

    def get_apiary_licence_document_history(self, obj):
        history = []
        for doc in obj.documents.all():
            history.append({"name": doc.name, "url": doc._file.url})
        return history

    def get_latest_apiary_licence_document(self, obj):
        url = ""
        if obj.documents.order_by("-uploaded_date"):
            url = obj.documents.order_by("-uploaded_date")[0]._file.url
        return url

    def get_application_type(self, obj):
        if obj.current_proposal.application_type:
            return obj.current_proposal.application_type.name
        return None

    def get_applicant(self, obj):
        try:
            if obj.proxy_applicant and obj.proxy_applicant.get_full_name():
                return obj.proxy_applicant.get_full_name()
            else:
                return obj.applicant.name if isinstance(obj.applicant, Organisation) else obj.applicant
        except:
            return None

    def get_applicant_id(self, obj):
        try:
            return obj.relevant_applicant_id
        except:
            return None

    def get_organisation(self, obj):
        try:
            organisation = obj.applicant
            if not isinstance(organisation, Organisation):
                return {}
            return {"name": organisation.name, "abn": organisation.abn}
        except Exception as e:
            logger.error(
                "Failed to serialize organisation for Approval id=%s: %s",
                obj.id,
                e,
            )
            return {}

    def get_applicant_first_name(self, obj):
        if obj.proxy_applicant:
            return obj.proxy_applicant.first_name

    def get_applicant_last_name(self, obj):
        if obj.proxy_applicant:
            return obj.proxy_applicant.last_name

    def get_applicant_address(self, obj):
        if obj.applicant:
            address = obj.applicant.address
            address_serializer = OrgAddressSerializer(address)
        elif obj.proxy_applicant:
            address = obj.proxy_applicant.residential_address
            address_serializer = ApplicantAddressSerializer(address)
        else:
            address = obj.current_proposal.submitter.residential_address
            address_serializer = ApplicantAddressSerializer(address)
        return address_serializer.data

    def get_renewal_document(self, obj):
        if obj.relevant_renewal_document and obj.relevant_renewal_document._file:
            return obj.relevant_renewal_document._file.url
        return None

    def get_can_approver_reissue(self, obj):
        # Check if currently logged in user has access to process the proposal
        request = self.context["request"]
        user = request.user
        if obj.can_reissue:
            if user in obj.allowed_approvers:
                return True
        return False

    def get_template_group(self, obj):
        return self.context.get("template_group")


from disturbance.components.proposals.serializers import ApprovalDTProposalSerializer


class DTApprovalSerializer(serializers.ModelSerializer):
    current_proposal = ApprovalDTProposalSerializer(read_only=True)
    allowed_assessors = EmailUserSerializer(many=True)
    licence_document = serializers.CharField(source="licence_document._file.url")
    # allowed_assessors = serializers.SerializerMethodField(read_only=True)
    can_approver_reissue = serializers.SerializerMethodField(read_only=True)
    latest_apiary_licence_document = serializers.SerializerMethodField()
    template_group = serializers.SerializerMethodField()
    applicant = serializers.SerializerMethodField(read_only=True)
    status = serializers.CharField(source="get_status_display")
    region = serializers.CharField(source="current_proposal.region")
    activity = serializers.SerializerMethodField(read_only=True)
    title = serializers.CharField(source="current_proposal.title")
    renewal_document = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Approval
        fields = (
            "id",
            "migrated",
            "activity",
            "region",
            "title",
            "status",
            "reference",
            "lodgement_number",
            "licence_document",
            "start_date",
            "expiry_date",
            "applicant",
            "can_reissue",
            "can_action",
            "can_reinstate",
            "can_amend",
            "can_renew",
            "set_to_cancel",
            "set_to_suspend",
            "set_to_surrender",
            "current_proposal",
            "current_proposal_id",
            "renewal_document",
            "renewal_sent",
            "allowed_assessors",
            "can_approver_reissue",
            "apiary_approval",
            "latest_apiary_licence_document",
            "template_group",
        )

        datatables_always_serialize = fields

    def get_allowed_assessors(self, obj):
        return EmailUserSerializer(obj.current_proposal.compliance_assessors, many=True).data

    def get_template_group(self, obj):
        return self.context.get("template_group")

    def get_latest_apiary_licence_document(self, obj):
        # 1. Grab all prefetched documents from memory
        docs = list(obj.documents.all())
        if not docs:
            return ""

        # 2. Sort them entirely in Python memory (No database hit!)
        # (Assuming 'uploaded_date' exists; if it throws an error, use 'id')
        docs.sort(key=lambda d: getattr(d, "uploaded_date", d.id) or d.id, reverse=True)

        try:
            return docs[0]._file.url
        except (IndexError, AttributeError, ValueError):
            return ""

    def get_renewal_document(self, obj):
        if obj.relevant_renewal_document and obj.relevant_renewal_document._file:
            return obj.relevant_renewal_document._file.url
        return None

    def get_can_approver_reissue(self, obj):
        # Check if currently logged in user has access to process the proposal
        request = self.context["request"]
        user = request.user
        if obj.can_reissue:
            if user in obj.allowed_approvers:
                return True
        return False

    def get_applicant(self, obj):
        try:
            if obj.proxy_applicant and obj.proxy_applicant.get_full_name():
                return obj.proxy_applicant.get_full_name()
            else:
                return obj.applicant.name if isinstance(obj.applicant, Organisation) else obj.applicant
        except:
            return None

    def get_activity(self, approval):
        activity_text = None
        if approval.apiary_approval:
            activity_text = "Apiary"
        else:
            activity_text = approval.current_proposal.activity
        return activity_text


class ApprovalCancellationSerializer(serializers.Serializer):
    cancellation_date = serializers.DateField(input_formats=["%d/%m/%Y", "%Y-%m-%d"])
    cancellation_details = serializers.CharField()


class ApprovalSuspensionSerializer(serializers.Serializer):
    from_date = serializers.DateField(input_formats=["%d/%m/%Y", "%Y-%m-%d"])
    to_date = serializers.DateField(input_formats=["%d/%m/%Y", "%Y-%m-%d"], required=False, allow_null=True)
    suspension_details = serializers.CharField()


class ApprovalSurrenderSerializer(serializers.Serializer):
    surrender_date = serializers.DateField(input_formats=["%d/%m/%Y", "%Y-%m-%d"])
    surrender_details = serializers.CharField()


class ApprovalUserActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source="who.get_full_name")

    class Meta:
        model = ApprovalUserAction
        fields = "__all__"


class ApprovalLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalLogEntry
        fields = "__all__"
        read_only_fields = ("customer",)

    def get_documents(self, obj):
        return [[d.name, d._file.url] for d in obj.documents.all()]

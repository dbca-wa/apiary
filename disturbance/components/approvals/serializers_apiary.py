import logging

from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from disturbance.components.approvals.models import ApiarySiteOnApproval
from disturbance.components.main.utils import get_region_district, get_status_for_export, get_tenure
from disturbance.components.organisations.models import Organisation

logger = logging.getLogger(__name__)


class ApiarySiteOnApprovalGeometrySerializer(GeoFeatureModelSerializer):
    """
    For reading
    """

    id = serializers.IntegerField(source="apiary_site.id")
    site_guid = serializers.CharField(source="apiary_site.site_guid")
    status = serializers.CharField(source="site_status")
    site_category = serializers.CharField(source="site_category.name")
    previous_site_holder_or_applicant = serializers.SerializerMethodField()
    is_vacant = serializers.BooleanField(source="apiary_site.is_vacant")
    stable_coords = serializers.SerializerMethodField()

    class Meta:
        model = ApiarySiteOnApproval
        geo_field = "wkb_geometry"
        fields = (
            "id",
            "site_guid",
            "available",
            "wkb_geometry",
            "site_category",
            "status",
            "is_vacant",
            "stable_coords",
            "previous_site_holder_or_applicant",
            "licensed_site",
            "batch_no",
            "approval_cpc_date",
            "approval_minister_date",
            "map_ref",
            "forest_block",
            "cog",
            "roadtrack",
            "zone",
            "catchment",
            "dra_permit",
        )

    def get_stable_coords(self, obj):
        return {"lng": obj.wkb_geometry.x, "lat": obj.wkb_geometry.y}

    def get_previous_site_holder_or_applicant(self, obj):
        try:
            relevant_applicant_name = obj.approval.relevant_applicant_name
            return relevant_applicant_name
        except:
            return ""


class ApiarySiteOnApprovalGeometryExportSerializer(ApiarySiteOnApprovalGeometrySerializer):
    site_id = serializers.IntegerField(source="apiary_site.id")
    status = serializers.SerializerMethodField()
    category = serializers.CharField(source="site_category.name", default="", read_only=True)
    surname = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    telephone = serializers.SerializerMethodField()
    mobile = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    organisation_name = serializers.SerializerMethodField()
    approval_lodgement_number = serializers.SerializerMethodField()
    proposal_lodgement_number = serializers.SerializerMethodField()

    # In-memory caches for the export run
    _approval_cache = {}
    _applicant_cache = {}
    _admin_cache = {}

    class Meta(ApiarySiteOnApprovalGeometrySerializer.Meta):
        fields = (
            "id",
            "site_id",
            "status",
            "category",
            "surname",
            "first_name",
            "address",
            "telephone",
            "mobile",
            "email",
            "organisation_name",
            "approval_lodgement_number",
            "proposal_lodgement_number",
        )

    def _get_approval_data(self, relation):
        """
        Extracts and caches all required strings once per approval/applicant.
        """
        approval = getattr(relation, "approval", None)
        if not approval:
            return {
                "lodgement_num": "",
                "org_name": "",
                "first_name": "",
                "last_name": "",
                "phone": "",
                "mobile": "",
                "email": "",
                "address": "",
            }

        app_id = approval.id
        if app_id in self._approval_cache:
            return self._approval_cache[app_id]

        lodgement_num = getattr(approval, "lodgement_number", "") or ""

        # Check cross-approval applicant cache key
        app_key = (
            getattr(approval, "org_applicant_id", None)
            or getattr(approval, "proxy_applicant_id", None)
            or getattr(approval, "applicant_id", None)
            or app_id
        )

        if app_key in self._applicant_cache:
            app_data = self._applicant_cache[app_key].copy()
            app_data["lodgement_num"] = lodgement_num
            self._approval_cache[app_id] = app_data
            return app_data

        # Initial fetch of applicant
        try:
            applicant = getattr(approval, "relevant_applicant", None)
        except Exception as e:
            logger.warning(f"[Approval {lodgement_num}] Failed fetching EmailUserRO/Organisation: {e}")
            applicant = None

        if not applicant:
            logger.warning(f"[Approval {lodgement_num}] (ID: {app_id}) has no valid applicant / EmailUserRO not found.")

        org_name = ""
        first_name = ""
        last_name = ""
        phone = ""
        mobile = ""

        if isinstance(applicant, Organisation):
            org_name = getattr(applicant, "name", "") or ""

            # Fetch / cache admin contact for Organisation
            org_id = getattr(applicant, "id", None)
            if org_id:
                if org_id not in self._admin_cache:
                    admins = applicant.contacts.filter(
                        user_status__in=("active", "suspended", "contact_form"),
                        is_admin=True,
                    )
                    self._admin_cache[org_id] = admins.first()
                admin = self._admin_cache[org_id]
                if admin:
                    first_name = getattr(admin, "first_name", "") or ""
                    last_name = getattr(admin, "last_name", "") or ""
                    phone = getattr(admin, "phone_number", "") or ""
                    mobile = getattr(admin, "mobile_number", phone) or ""

        elif isinstance(applicant, EmailUser):
            first_name = getattr(applicant, "first_name", "") or ""
            last_name = getattr(applicant, "last_name", "") or ""
            phone = getattr(applicant, "phone_number", "") or ""
            mobile = getattr(applicant, "mobile_number", phone) or ""

        # Address
        try:
            addr = approval.relevant_applicant_address
            address_str = ", ".join(str(v) for v in addr.values() if v) if isinstance(addr, dict) else str(addr or "")
        except Exception:
            address_str = ""

        # Email
        try:
            email_str = approval.relevant_applicant_email or ""
        except Exception:
            email_str = ""

        data = {
            "lodgement_num": lodgement_num,
            "org_name": org_name,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "mobile": mobile,
            "email": email_str,
            "address": address_str,
        }

        self._applicant_cache[app_key] = data
        self._approval_cache[app_id] = data
        return data

    def get_approval_lodgement_number(self, relation):
        return self._get_approval_data(relation)["lodgement_num"]

    def get_proposal_lodgement_number(self, relation):
        return ""

    def get_organisation_name(self, relation):
        return self._get_approval_data(relation)["org_name"]

    def get_status(self, relation):
        return get_status_for_export(relation)

    def get_surname(self, relation):
        return self._get_approval_data(relation)["last_name"]

    def get_first_name(self, relation):
        return self._get_approval_data(relation)["first_name"]

    def get_address(self, relation):
        return self._get_approval_data(relation)["address"]

    def get_telephone(self, relation):
        return self._get_approval_data(relation)["phone"]

    def get_mobile(self, relation):
        return self._get_approval_data(relation)["mobile"]

    def get_email(self, relation):
        return self._get_approval_data(relation)["email"]


class ApiarySiteOnApprovalLicenceDocSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="apiary_site.id")
    # site_category = serializers.CharField(source='site_category.name')
    site_category = serializers.SerializerMethodField()
    coords = serializers.SerializerMethodField()
    tenure = serializers.SerializerMethodField()
    region_district = serializers.SerializerMethodField()
    licensed_site = serializers.SerializerMethodField()
    batch_no = serializers.SerializerMethodField()
    approval_cpc_date = serializers.SerializerMethodField()
    approval_minister_date = serializers.SerializerMethodField()
    map_ref = serializers.SerializerMethodField()
    forest_block = serializers.SerializerMethodField()
    cog = serializers.SerializerMethodField()
    roadtrack = serializers.SerializerMethodField()
    zone = serializers.SerializerMethodField()
    catchment = serializers.SerializerMethodField()
    dra_permit = serializers.SerializerMethodField()
    fee_application = serializers.SerializerMethodField()
    # annual_site_fee = serializers.SerializerMethodField()
    fee_renewal = serializers.SerializerMethodField()
    fee_transfer = serializers.SerializerMethodField()

    class Meta:
        model = ApiarySiteOnApproval

        fields = (
            "id",
            "coords",
            "site_category",
            "tenure",
            "region_district",
            "licensed_site",
            "batch_no",
            "approval_cpc_date",
            "approval_minister_date",
            "map_ref",
            "forest_block",
            "cog",
            "roadtrack",
            "zone",
            "catchment",
            "dra_permit",
            "fee_application",
            # 'annual_site_fee',
            "fee_renewal",
            "fee_transfer",
        )

    def get_site_category(self, apiary_site_on_approval):
        site_category = apiary_site_on_approval.site_category
        return site_category.display_name

    def get_tenure(self, apiary_site_on_approval):
        try:
            res = get_tenure(apiary_site_on_approval.wkb_geometry)
            return res
        except:
            return ""

    def get_region_district(self, apiary_site_on_approval):
        try:
            res = get_region_district(apiary_site_on_approval.wkb_geometry)
            return res
        except:
            return ""

    def get_coords(self, apiary_site_on_approval):
        try:
            return {"lng": apiary_site_on_approval.wkb_geometry.x, "lat": apiary_site_on_approval.wkb_geometry.y}
        except:
            return {"lng": "", "lat": ""}

    def get_licensed_site(self, apiary_site_on_proposal):
        try:
            return apiary_site_on_proposal.licensed_site
        except:
            return ""

    def get_batch_no(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.batch_no if apiary_site_on_proposal.batch_no else ""

    def get_approval_cpc_date(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.approval_cpc_date if apiary_site_on_proposal.approval_cpc_date else ""

    def get_approval_minister_date(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.approval_minister_date if apiary_site_on_proposal.approval_minister_date else ""

    def get_map_ref(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.map_ref if apiary_site_on_proposal.map_ref else ""

    def get_forest_block(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.forest_block if apiary_site_on_proposal.forest_block else ""

    def get_cog(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.cog if apiary_site_on_proposal.cog else ""

    def get_roadtrack(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.roadtrack if apiary_site_on_proposal.roadtrack else ""

    def get_zone(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.zone if apiary_site_on_proposal.zone else ""

    def get_catchment(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.catchment if apiary_site_on_proposal.catchment else ""

    def get_dra_permit(self, apiary_site_on_proposal):
        return "Yes" if apiary_site_on_proposal.dra_permit else "No"

    def get_fee_application(self, apiary_site_on_approval):
        # return apiary_site_on_approval.site_category.fee_application_per_site  # This is application fee
        return self.get_annual_site_fee(apiary_site_on_approval)

    def get_annual_site_fee(self, apiary_site_on_approval):

        from disturbance.components.proposals.models import ApiaryAnnualRentalFee, SiteCategory

        fees_applied = ApiaryAnnualRentalFee.get_fees_by_period(
            apiary_site_on_approval.approval.start_date, apiary_site_on_approval.approval.expiry_date
        )  # Fee may be changed during the period.  That's why fees_applied is an array.
        # num_of_days_in_period = apiary_site_on_approval.approval.expiry_date - (apiary_site_on_approval.approval.start_date - timedelta(days=1))
        num_of_days_in_year = 365

        if apiary_site_on_approval.site_category.name == SiteCategory.CATEGORY_SOUTH_WEST:
            key_for_amount = "amount_south_west_per_year"
        else:
            key_for_amount = "amount_remote_per_year"

        annual_site_fee = 0
        for fee_for_site in fees_applied:
            # annual_site_fee += fee_for_site.get(key_for_amount) * fee_for_site.get('num_of_days').days / num_of_days_in_year
            # annual_site_fee = round_amount_according_to_env(annual_site_fee)
            annual_site_fee = fee_for_site.get(key_for_amount)  # We just display the 1st one
            break

        return annual_site_fee

    def get_fee_renewal(self, apiary_site_on_approval):
        return apiary_site_on_approval.site_category.fee_renewal_per_site

    def get_fee_transfer(self, apiary_site_on_approval):
        return apiary_site_on_approval.site_category.fee_transfer_per_site

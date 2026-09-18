from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from disturbance.components.approvals.models import ApiarySiteOnApproval
from disturbance.components.ap_payments.utils import round_amount_according_to_env
from disturbance.components.main.utils import get_category, get_tenure, get_region_district, get_status_for_export
from disturbance.components.organisations.models import Organisation


class ApiarySiteOnApprovalGeometrySerializer(GeoFeatureModelSerializer):
    """
    For reading
    """
    id = serializers.IntegerField(source='apiary_site.id')
    site_guid = serializers.CharField(source='apiary_site.site_guid')
    status = serializers.CharField(source='site_status')
    site_category = serializers.CharField(source='site_category.name')
    previous_site_holder_or_applicant = serializers.SerializerMethodField()
    is_vacant = serializers.BooleanField(source='apiary_site.is_vacant')
    stable_coords = serializers.SerializerMethodField()

    class Meta:
        model = ApiarySiteOnApproval
        geo_field = 'wkb_geometry'
        fields = (
            'id',
            'site_guid',
            'available',
            'wkb_geometry',
            'site_category',
            'status',
            'is_vacant',
            'stable_coords',
            'previous_site_holder_or_applicant',
            'licensed_site',
            'batch_no',
            'approval_cpc_date',
            'approval_minister_date',
            'map_ref',
            'forest_block',
            'cog',
            'roadtrack',
            'zone',
            'catchment',
            'dra_permit',
        )

    def get_stable_coords(self, obj):
        return {'lng': obj.wkb_geometry.x, 'lat': obj.wkb_geometry.y}

    def get_previous_site_holder_or_applicant(self, obj):
        try:
            relevant_applicant_name = obj.approval.relevant_applicant_name
            return relevant_applicant_name
        except:
            return ''


class ApiarySiteOnApprovalGeometryExportSerializer(ApiarySiteOnApprovalGeometrySerializer):
    site_id = serializers.IntegerField(source='apiary_site.id')
    status = serializers.SerializerMethodField()
    category = serializers.CharField(source='site_category.name')
    surname = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    telephone = serializers.SerializerMethodField()
    mobile = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    organisation_name = serializers.SerializerMethodField()
    approval_lodgement_number = serializers.CharField(source='approval.lodgement_number')
    proposal_lodgement_number = serializers.SerializerMethodField()

    class Meta(ApiarySiteOnApprovalGeometrySerializer.Meta):
        fields = (
            'id',
            'site_id',
            'status',
            'category',
            'surname',
            'first_name',
            'address',
            'telephone',
            'mobile',
            'email',
            'organisation_name',
            'approval_lodgement_number',
            'proposal_lodgement_number',
        )

    def get_proposal_lodgement_number(self, obj):
        return ''

    def get_organisation_name(self, relation):
        relevant_applicant = relation.approval.relevant_applicant
        if isinstance(relevant_applicant, Organisation):
            return relevant_applicant.name
        else:
            return ''

    def get_status(self, relation):
        return get_status_for_export(relation)

    def _get_admin_user(self, org):
        admins = org.contacts.filter(user_status__in=('active', 'suspended', 'contact_form',), is_admin=True)
        admin = admins.first() if admins else None
        return admin

    def get_surname(self, relation):
        relevant_applicant = relation.approval.relevant_applicant
        if isinstance(relevant_applicant, EmailUser):
            return relevant_applicant.last_name
        elif isinstance(relevant_applicant, Organisation):
            admin = self._get_admin_user(relevant_applicant)
            if admin:
                return admin.last_name
            else:
                return ''
        else:
            return ''

    def get_first_name(self, relation):
        relevant_applicant = relation.approval.relevant_applicant
        if isinstance(relevant_applicant, EmailUser):
            return relevant_applicant.first_name
        elif isinstance(relevant_applicant, Organisation):
            admin = self._get_admin_user(relevant_applicant)
            if admin:
                return admin.first_name
            else:
                return ''
        else:
            return ''

    def get_address(self, relation):
        try:
            address = relation.approval.relevant_applicant_address
            return ", ".join(address.values())
        except:
            return ''

    def get_telephone(self, relation):
        relevant_applicant = relation.approval.relevant_applicant
        if isinstance(relevant_applicant, EmailUser):
            return relevant_applicant.phone_number
        elif isinstance(relevant_applicant, Organisation):
            admin = self._get_admin_user(relevant_applicant)
            if admin:
                return admin.phone_number
            else:
                return ''
        else:
            return ''

    def get_mobile(self, relation):
        relevant_applicant = relation.approval.relevant_applicant
        if isinstance(relevant_applicant, EmailUser):
            return relevant_applicant.phone_number
        elif isinstance(relevant_applicant, Organisation):
            admin = self._get_admin_user(relevant_applicant)
            if admin:
                return admin.mobile_number
            else:
                return ''
        else:
            return ''

    def get_email(self, relation):
        return relation.approval.relevant_applicant_email


class ApiarySiteOnApprovalLicenceDocSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='apiary_site.id')
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
            'id',
            'coords',
            'site_category',
            'tenure',
            'region_district',
            'licensed_site',
            'batch_no',
            'approval_cpc_date',
            'approval_minister_date',
            'map_ref',
            'forest_block',
            'cog',
            'roadtrack',
            'zone',
            'catchment',
            'dra_permit',
            'fee_application',
            # 'annual_site_fee',
            'fee_renewal',
            'fee_transfer',
        )

    def get_site_category(self, apiary_site_on_approval):
        site_category = apiary_site_on_approval.site_category
        return site_category.display_name

    def get_tenure(self, apiary_site_on_approval):
        try:
            res = get_tenure(apiary_site_on_approval.wkb_geometry)
            return res
        except:
            return ''

    def get_region_district(self, apiary_site_on_approval):
        try:
            res = get_region_district(apiary_site_on_approval.wkb_geometry)
            return res
        except:
            return ''

    def get_coords(self, apiary_site_on_approval):
        try:
            return {'lng': apiary_site_on_approval.wkb_geometry.x, 'lat': apiary_site_on_approval.wkb_geometry.y}
        except:
            return {'lng': '', 'lat': ''}

    def get_licensed_site(self, apiary_site_on_proposal):
        try:
            return apiary_site_on_proposal.licensed_site
        except:
            return ''

    def get_batch_no(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.batch_no if apiary_site_on_proposal.batch_no else ''

    def get_approval_cpc_date(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.approval_cpc_date if apiary_site_on_proposal.approval_cpc_date else ''

    def get_approval_minister_date(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.approval_minister_date if apiary_site_on_proposal.approval_minister_date else ''

    def get_map_ref(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.map_ref if apiary_site_on_proposal.map_ref else ''

    def get_forest_block(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.forest_block if apiary_site_on_proposal.forest_block else ''

    def get_cog(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.cog if apiary_site_on_proposal.cog else ''

    def get_roadtrack(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.roadtrack if apiary_site_on_proposal.roadtrack else ''

    def get_zone(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.zone if apiary_site_on_proposal.zone else ''

    def get_catchment(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.catchment if apiary_site_on_proposal.catchment else ''

    def get_dra_permit(self, apiary_site_on_proposal):
        return 'Yes' if apiary_site_on_proposal.dra_permit else 'No'

    def get_fee_application(self, apiary_site_on_approval):
        # return apiary_site_on_approval.site_category.fee_application_per_site  # This is application fee
        return self.get_annual_site_fee(apiary_site_on_approval)

    def get_annual_site_fee(self, apiary_site_on_approval):
        from disturbance.components.proposals.models import ApiaryAnnualRentalFee, SiteCategory
        from datetime import timedelta

        fees_applied = ApiaryAnnualRentalFee.get_fees_by_period(apiary_site_on_approval.approval.start_date, apiary_site_on_approval.approval.expiry_date)  # Fee may be changed during the period.  That's why fees_applied is an array.
        # num_of_days_in_period = apiary_site_on_approval.approval.expiry_date - (apiary_site_on_approval.approval.start_date - timedelta(days=1))
        num_of_days_in_year = 365

        if apiary_site_on_approval.site_category.name == SiteCategory.CATEGORY_SOUTH_WEST:
            key_for_amount = 'amount_south_west_per_year'
        else:
            key_for_amount = 'amount_remote_per_year'

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



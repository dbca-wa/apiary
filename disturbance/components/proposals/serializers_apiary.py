from copy import deepcopy
from datetime import datetime

import pytz
from confy import env
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils import timezone
from ledger_api_client.ledger_models import Address
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from reversion.models import Version

from disturbance.components.approvals.models import Approval
from disturbance.components.approvals.serializers_apiary import ApiarySiteOnApprovalGeometrySerializer
from disturbance.components.main.utils import (
    get_category,
    get_feature_in_wa_coastline_smoothed,
    get_region_district,
    get_status_for_export,
    get_tenure,
    validate_buffer,
)
from disturbance.components.organisations.models import Organisation, UserDelegation
from disturbance.components.organisations.serializers import OrganisationSerializer
from disturbance.components.proposals.models import (
    ApiaryChecklistAnswer,
    ApiaryChecklistQuestion,
    ApiaryReferral,
    ApiaryReferralGroup,
    ApiarySite,
    ApiarySiteFee,
    ApiarySiteFeeRemainder,
    ApiarySiteFeeType,
    ApiarySiteOnProposal,
    OnSiteInformation,
    Proposal,
    ProposalApiary,
    ProposalApiaryDocument,
    ProposalApiaryTemporaryUse,
    ProposalRequirement,
    Referral,
    SiteCategory,
    TemporaryUseApiarySite,
)
from disturbance.components.proposals.serializers_base import (
    BaseProposalSerializer,
    EmailUserSerializer,
    ProposalDeclinedDetailsSerializer,
)
from disturbance.helpers import is_internal


class VersionSerializer(serializers.ModelSerializer):
    proposal_fields = serializers.SerializerMethodField()
    date_modified = serializers.SerializerMethodField()
    class Meta:
        model = Version
        fields = (
                'id',
                'revision',
                'proposal_fields',
                'date_modified',
                )
        read_only_fields = (
                'id',
                'revision',
                'proposal_fields',
                'date_modified',
                )

    def get_date_modified(self, obj):
        date_modified = None
        if obj.revision and obj.revision.date_created:
            date_modified = timezone.localtime(obj.revision.date_created)
        return date_modified

    def get_proposal_fields(self, obj):
        proposal_data = []
        if obj.revision:
            apiary_sites = []
            for record in obj.revision.version_set.all():
                if record.object:
                    # Exclude these models from the result
                    if record.object._meta.model_name in [
                            'proposallogentry',
                            'annualrentalfee',
                            'approvaldocument',
                            'approval',
                            ]:
                        continue
                    elif ContentType.objects.get(id=record.content_type_id).model == 'apiarysite':
                        payload = deepcopy(record.field_dict)
                        # Exclude these fields from the result
                        payload.pop("wkb_geometry", None)
                        payload.pop("wkb_geometry_applied", None)
                        payload.pop("wkb_geometry_pending", None)
                        payload.pop("objects", None)
                        payload.pop("site_guid", None)
                        wkb_geometry = record.field_dict.get('wkb_geometry')
                        if wkb_geometry:
                            payload['coords'] = {'lng': wkb_geometry.x, 'lat': wkb_geometry.y}
                        wkb_geometry_pending = record.field_dict.get('wkb_geometry_pending')
                        if wkb_geometry_pending:
                            payload['pending_coords'] = {'lng': wkb_geometry_pending.x, 'lat': wkb_geometry_pending.y}
                        apiary_sites.append({record.object._meta.model_name: payload})
                    else:
                        proposal_data.append({record.object._meta.model_name: record.field_dict})
            proposal_data.append({'apiary_sites': apiary_sites})
        return proposal_data


class ProposalHistorySerializer(serializers.ModelSerializer):
    versions = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = (
                'id',
                'versions',
                )

    def get_versions(self, obj):
        entry_versions = VersionSerializer(
                Version.objects.get_for_object(obj),
                many=True)
        return entry_versions.data


class ApiaryChecklistQuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ApiaryChecklistQuestion
        fields=('id',
                'text',
                'answer_type',
                'checklist_type',
                'order'
                )


class ApiarySiteOnProposalChecklistSerializer(serializers.ModelSerializer):

    site_category = serializers.CharField(source='site_category_processed.name')

    class Meta:
        model = ApiarySiteOnProposal

        fields = (
            'id',
            'apiary_site_id',
            'site_category',
            'licensed_site',
        )


class ApiaryChecklistAnswerSerializer(serializers.ModelSerializer):
    question = ApiaryChecklistQuestionSerializer()

    class Meta:
        model = ApiaryChecklistAnswer
        fields=('id',
                'question',
                'answer',
                'proposal_id',
                'apiary_referral_id',
                'text_answer',
                'apiary_site_id'
                )


class ApplicantAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            'id',
            'line1',
            'line2',
            'line3',
            'locality',
            'state',
            'country',
            'postcode'
        )

class OrgAddressSerializer(serializers.Serializer):
    line1 = serializers.CharField()
    locality = serializers.CharField()
    state = serializers.CharField()
    postcode = serializers.CharField()
    country = serializers.CharField()

class OnSiteInformationSerializer(serializers.ModelSerializer):
    apiary_site_id = serializers.IntegerField(read_only=True, source='apiary_site_on_approval.apiary_site.id')
    apiary_site_on_approval_id = serializers.IntegerField(required=False)
    datetime_deleted = serializers.DateTimeField(write_only=True, required=False)

    class Meta:
        model = OnSiteInformation
        fields = (
            'id',
            'apiary_site_id',
            'apiary_site_on_approval_id',
            'period_from',
            'period_to',
            'hives_loc',
            'hives_num',
            'people_names',
            'flora',
            'comments',
            'datetime_deleted',
        )

    def validate(self, data):
        field_errors = {}
        non_field_errors = []

        if not self.partial:
            if not data['period_from']:
                field_errors['Period from'] = ['Please select a date.',]
            if not data['period_to']:
                field_errors['Period to'] = ['Please select a date.',]

            if not data['comments']:
                field_errors['comments'] = ['Please enter comments.',]

            # Raise errors
            if field_errors:
                raise serializers.ValidationError(field_errors)

            if data['period_from'] > data['period_to']:
                non_field_errors.append('Period "from" date must be before "to" date.')

            # Raise errors
            if non_field_errors:
                raise serializers.ValidationError(non_field_errors)

        return data

class ApiarySiteOnProposalDraftGeometrySerializer(GeoFeatureModelSerializer):
    """
    For reading as 'draft'
    """
    id = serializers.IntegerField(source='apiary_site.id')
    site_guid = serializers.CharField(source='apiary_site.site_guid')
    status = serializers.CharField(source='site_status')
    site_category = serializers.CharField(source='site_category_draft.name')
    previous_site_holder_or_applicant = serializers.SerializerMethodField()
    is_vacant = serializers.BooleanField(source='apiary_site.is_vacant')
    stable_coords = serializers.SerializerMethodField()
    #batch_no = serializers.CharField(source='apiary_site.batch_no')

    class Meta:
        model = ApiarySiteOnProposal
        geo_field = 'wkb_geometry_draft'
        fields = (
            'id',
            'site_guid',
            'is_vacant',
            'wkb_geometry_draft',
            'site_category',
            'status',
            'workflow_selected_status',
            'for_renewal',
            'previous_site_holder_or_applicant',
            'making_payment',
            'stable_coords',
            'application_fee_paid',
            'apiary_site_status_when_submitted',
            'apiary_site_is_vacant_when_submitted',
            'licensed_site',
            'issuance_details',
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
        return {'lng': obj.wkb_geometry_draft.x, 'lat': obj.wkb_geometry_draft.y}

    def get_previous_site_holder_or_applicant(self, obj):
        try:
            relevant_applicant_name = obj.proposal_apiary.proposal.relevant_applicant_name
            return relevant_applicant_name
        except:
            return ''


class ApiarySiteOnProposalDraftGeometryExportSerializer(ApiarySiteOnProposalDraftGeometrySerializer):
    """
    For export draft
    """
    site_id = serializers.IntegerField(source='apiary_site.id')
    status = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    surname = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    telephone = serializers.SerializerMethodField()
    mobile = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    organisation_name = serializers.SerializerMethodField()
    proposal_lodgement_number = serializers.SerializerMethodField()
    approval_lodgement_number = serializers.SerializerMethodField()

    class Meta(ApiarySiteOnProposalDraftGeometrySerializer.Meta):
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
            'proposal_lodgement_number',
            'approval_lodgement_number',
        )

    def get_proposal_lodgement_number(self, obj):
        if obj.proposal_apiary and obj.proposal_apiary.proposal:
            return obj.proposal_apiary.proposal.lodgement_number
        else:
            return ''

    def get_approval_lodgement_number(self, obj):
        return ''

    def get_organisation_name(self, relation):
        relevant_applicant = relation.proposal_apiary.proposal.relevant_applicant
        if isinstance(relevant_applicant, Organisation):
            return relevant_applicant.organisation.name
        else:
            return ''

    def get_status(self, relation):
        return get_status_for_export(relation)

    def get_category(self, relation):
        return relation.site_category_draft.name

    def get_surname(self, relation):
        relevant_applicant = relation.proposal_apiary.proposal.relevant_applicant
        if isinstance(relevant_applicant, EmailUser):
            return relevant_applicant.last_name
        else:
            return ''

    def get_first_name(self, relation):
        relevant_applicant = relation.proposal_apiary.proposal.relevant_applicant
        if isinstance(relevant_applicant, EmailUser):
            return relevant_applicant.first_name
        else:
            return ''

    def get_address(self, relation):
        try:
            address = relation.proposal_apiary.proposal.relevant_applicant_address
            return ", ".join(address.values())
        except:
            return ''

    def get_telephone(self, relation):
        relevant_applicant = relation.proposal_apiary.proposal.relevant_applicant
        if isinstance(relevant_applicant, EmailUser):
            return relevant_applicant.phone_number
        else:
            return ''

    def get_mobile(self, relation):
        relevant_applicant = relation.proposal_apiary.proposal.relevant_applicant
        if isinstance(relevant_applicant, EmailUser):
            return relevant_applicant.phone_number
        else:
            return ''

    def get_email(self, relation):
        return relation.proposal_apiary.proposal.relevant_applicant_email


class ApiarySiteOnProposalProcessedGeometrySerializer(GeoFeatureModelSerializer):
    """
    For reading as 'processed'
    """
    id = serializers.IntegerField(source='apiary_site.id')
    site_guid = serializers.CharField(source='apiary_site.site_guid')
    status = serializers.SerializerMethodField()
    site_category = serializers.SerializerMethodField()
    previous_site_holder_or_applicant = serializers.SerializerMethodField()
    is_vacant = serializers.BooleanField(source='apiary_site.is_vacant')
    stable_coords = serializers.SerializerMethodField()

    class Meta:
        model = ApiarySiteOnProposal
        geo_field = 'wkb_geometry_processed'
        fields = (
            'id',
            'site_guid',
            'is_vacant',
            'wkb_geometry_processed',
            'site_category',
            'status',
            'workflow_selected_status',
            'for_renewal',
            'making_payment',
            'previous_site_holder_or_applicant',
            'stable_coords',
            'application_fee_paid',
            'apiary_site_status_when_submitted',
            'apiary_site_is_vacant_when_submitted',
            'licensed_site',
            'issuance_details',
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
        {'lng': obj.wkb_geometry_processed.x, 'lat': obj.wkb_geometry_processed.y}

    def get_status(self, apiary_site_on_proposal):
        # if apiary_site_on_proposal.apiary_site.is_vacant:
        #     return SITE_STATUS_VACANT
        return apiary_site_on_proposal.site_status

    def get_site_category(self, apiary_site_on_proposal):
        return apiary_site_on_proposal.site_category_processed.name

    def get_previous_site_holder_or_applicant(self, apiary_site_on_proposal):
        try:
            relevant_applicant_name = apiary_site_on_proposal.proposal_apiary.proposal.relevant_applicant_name
            return relevant_applicant_name
        except:
            return ''


class ApiarySiteOnProposalProcessedGeometryExportSerializer(ApiarySiteOnProposalProcessedGeometrySerializer):
    """
    For export draft
    """
    site_id = serializers.IntegerField(source='apiary_site.id')
    status = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    surname = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    telephone = serializers.SerializerMethodField()
    mobile = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    organisation_name = serializers.SerializerMethodField()
    proposal_lodgement_number = serializers.SerializerMethodField()
    approval_lodgement_number = serializers.SerializerMethodField()

    class Meta(ApiarySiteOnProposalProcessedGeometrySerializer.Meta):
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
            'proposal_lodgement_number',
            'approval_lodgement_number',
        )

    def get_proposal_lodgement_number(self, obj):
        if obj.proposal_apiary and obj.proposal_apiary.proposal:
            return obj.proposal_apiary.proposal.lodgement_number
        else:
            return ''

    def get_approval_lodgement_number(self, obj):
        return ''

    def get_organisation_name(self, relation):
        relevant_applicant = relation.proposal_apiary.proposal.relevant_applicant
        if isinstance(relevant_applicant, Organisation):
            return relevant_applicant.organisation.name
        else:
            return ''

    def get_status(self, relation):
        return get_status_for_export(relation)

    def get_category(self, relation):
        return relation.site_category_draft.name

    def get_surname(self, relation):
        relevant_applicant = relation.proposal_apiary.proposal.relevant_applicant
        if isinstance(relevant_applicant, EmailUser):
            return relevant_applicant.last_name
        else:
            return ''

    def get_first_name(self, relation):
        relevant_applicant = relation.proposal_apiary.proposal.relevant_applicant
        if isinstance(relevant_applicant, EmailUser):
            return relevant_applicant.first_name
        else:
            return ''

    def get_address(self, relation):
        try:
            address = relation.proposal_apiary.proposal.relevant_applicant_address
            return ", ".join(address.values())
        except:
            return ''

    def get_telephone(self, relation):
        relevant_applicant = relation.proposal_apiary.proposal.relevant_applicant
        if isinstance(relevant_applicant, EmailUser):
            return relevant_applicant.phone_number
        else:
            return ''

    def get_mobile(self, relation):
        relevant_applicant = relation.proposal_apiary.proposal.relevant_applicant
        if isinstance(relevant_applicant, EmailUser):
            return relevant_applicant.phone_number
        else:
            return ''

    def get_email(self, relation):
        return relation.proposal_apiary.proposal.relevant_applicant_email


class ApiarySiteOnProposalDraftGeometrySaveSerializer(GeoFeatureModelSerializer):
    """
    For saving as 'draft'
    """
    def validate(self, attrs):
        wkb_geometry = attrs.get('wkb_geometry_draft')

        check_coastline = env('PERFORM_BACKEND_COAST_LINE_CHECK', False)
        if check_coastline:
            feature = get_feature_in_wa_coastline_smoothed(wkb_geometry)
            if not feature:
                raise serializers.ValidationError([f'Apiary Site: {self.instance.apiary_site.id} (lat: {wkb_geometry.coords[1]}, lng: {wkb_geometry.coords[0]}) is out of bounds.'])

        apiary_sites_to_exclude = [self.instance.apiary_site,] if self.instance.apiary_site else None

        #validate_buffer(wkb_geometry, apiary_sites_to_exclude)
        if not self.instance.apiary_site.exempt_from_radius_restriction:
            validate_buffer(wkb_geometry, apiary_sites_to_exclude)

        site_category = get_category(attrs['wkb_geometry_draft'])
        attrs['site_category_draft'] = site_category
        return attrs

    class Meta:
        model = ApiarySiteOnProposal
        geo_field = 'wkb_geometry_draft'
        fields = (
            'wkb_geometry_draft',
            'workflow_selected_status',
            'site_category_draft',
        )


class ApiarySiteOnProposalProcessedGeometrySaveSerializer(GeoFeatureModelSerializer):
    """
    For saving as 'processed'
    """
    def validate(self, attrs):
        # TODO on cleanup: review (old comment) validate 3km radius, etc
        site_category = get_category(attrs['wkb_geometry_processed'])
        attrs['site_category_processed'] = site_category
        return attrs

    class Meta:
        model = ApiarySiteOnProposal
        geo_field = 'wkb_geometry_processed'
        fields = (
            'wkb_geometry_processed',
            'site_category_processed',
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

class ApiarySiteOnProposalProcessedLicensedSiteSaveSerializer(serializers.ModelSerializer):
    """
    For saving as 'processed'
    """
    class Meta:
        model = ApiarySiteOnProposal
        fields = (
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


class ApiarySiteSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        return attrs

    class Meta:
        model = ApiarySite
        fields = (
            'id',
            'site_guid',
        )


class ProposalApiarySerializer(serializers.ModelSerializer):

    applicant_checklist_answers = serializers.SerializerMethodField()
    assessor_checklist_answers = serializers.SerializerMethodField()
    assessor_checklist_answers_per_site = serializers.SerializerMethodField()
    referrer_checklist_answers = serializers.SerializerMethodField()
    referrer_checklist_answers_per_site = serializers.SerializerMethodField()
    site_transfer_assessor_checklist_answers = serializers.SerializerMethodField()
    site_transfer_assessor_checklist_answers_per_site = serializers.SerializerMethodField()
    site_transfer_referrer_checklist_answers = serializers.SerializerMethodField()
    site_transfer_referrer_checklist_answers_per_site = serializers.SerializerMethodField()
    site_remainders = serializers.SerializerMethodField()
    originating_approval_lodgement_number = serializers.SerializerMethodField()
    originating_approval_licence_document = serializers.SerializerMethodField()
    originating_approval_name = serializers.SerializerMethodField()
    originating_approval_reissued = serializers.SerializerMethodField()
    target_approval_lodgement_number = serializers.SerializerMethodField()
    target_approval_licence_document = serializers.SerializerMethodField()
    target_approval_name = serializers.SerializerMethodField()
    target_approval_reissued = serializers.SerializerMethodField()
    transferee_name = serializers.SerializerMethodField()
    transferee_org_name = serializers.SerializerMethodField()
    transferee_first_name = serializers.SerializerMethodField()
    transferee_last_name = serializers.SerializerMethodField()

    class Meta:
        model = ProposalApiary
        fields = (
            'id',
            'proposal',
            'longitude',
            'latitude',
            'applicant_checklist_answers',
            'assessor_checklist_answers',
            'assessor_checklist_answers_per_site',
            'referrer_checklist_answers',
            'referrer_checklist_answers_per_site',
            'site_transfer_assessor_checklist_answers',
            'site_transfer_assessor_checklist_answers_per_site',
            'site_transfer_referrer_checklist_answers',
            'site_transfer_referrer_checklist_answers_per_site',
            'site_remainders',
            'originating_approval_id',
            'originating_approval_lodgement_number',
            'originating_approval_licence_document',
            'originating_approval_name',
            'originating_approval_reissued',
            'target_approval_id',
            'target_approval_lodgement_number',
            'target_approval_licence_document',
            'target_approval_name',
            'target_approval_reissued',
            'transferee_name',
            'transferee_org_name',
            'transferee_first_name',
            'transferee_last_name',
            'transferee_email_text',
            'transferee_id',
            'target_approval_organisation_id',
            'public_liability_insurance_expiry_date',
            'reissue_originating_approval',
            'reissue_target_approval',
        )

    def get_originating_approval_reissued(self,obj):
        if obj.originating_approval:
            return obj.originating_approval.reissued

    def get_target_approval_reissued(self,obj):
        if obj.target_approval:
            return obj.target_approval.reissued

    def get_originating_approval_name(self,obj):
        if obj.originating_approval:
            return obj.originating_approval.relevant_applicant_name

    def get_target_approval_name(self,obj):
        if obj.target_approval:
            return obj.target_approval.relevant_applicant_name

    def validate(self, attrs):
        self.instance.validate_apiary_sites(raise_exception=True)
        return attrs

    def get_originating_approval_licence_document(self, proposal_apiary):
        url = ''
        if proposal_apiary.originating_approval:
            url = proposal_apiary.originating_approval.documents.order_by('-uploaded_date')[0]._file.url
        return url

    def get_target_approval_licence_document(self, proposal_apiary):
        url = ''
        if proposal_apiary.target_approval and proposal_apiary.target_approval.documents.count():
            url = proposal_apiary.target_approval.documents.order_by('-uploaded_date')[0]._file.url
        return url

    def get_transferee_name(self, obj):
        name = None
        #if obj.proposal.approval:
         #   name = obj.proposal.approval.relevant_applicant_name
        if obj.target_approval:
            name = obj.target_approval.relevant_applicant_name
        elif obj.transferee:
            name = obj.transferee.get_full_name()
        return name

    def get_transferee_org_name(self, obj):
        name = None
        if obj.target_approval and obj.target_approval.applicant:
            name = obj.target_approval.applicant.name
        elif obj.target_approval_organisation:
            name = obj.target_approval_organisation.name
        return name

    def get_transferee_first_name(self, obj):
        name = None
        if obj.target_approval and obj.target_approval.proxy_applicant:
            name = obj.target_approval.proxy_applicant.first_name
        elif obj.transferee:
            name = obj.transferee.first_name
        return name

    def get_transferee_last_name(self, obj):
        name = None
        if obj.target_approval and obj.target_approval.proxy_applicant:
            name = obj.target_approval.proxy_applicant.last_name
        elif obj.transferee:
            name = obj.transferee.last_name
        return name

    def get_target_approval_lodgement_number(self, obj):
        lodgement_number = None
        if obj.target_approval:
            #lodgement_number = obj.proposal.approval.lodgement_number
            lodgement_number = obj.target_approval.lodgement_number
        return lodgement_number

    def get_originating_approval_lodgement_number(self, obj):
        lodgement_number = None
        if obj.originating_approval:
            lodgement_number = obj.originating_approval.lodgement_number
        return lodgement_number

    def get_site_remainders(self, proposal_apiary):
        today_local = datetime.now(pytz.timezone(settings.TIME_ZONE)).date()

        ret_list = []
        for category in SiteCategory.CATEGORY_CHOICES:
            try:
                # Retrieve sites left
                filter_site_category = Q(site_category__name=category[0])
                filter_site_fee_type = Q(apiary_site_fee_type=ApiarySiteFeeType.objects.get(name=ApiarySiteFeeType.FEE_TYPE_APPLICATION))
                filter_applicant = Q(applicant=proposal_apiary.proposal.applicant)
                filter_proxy_applicant = Q(proxy_applicant=proposal_apiary.proposal.proxy_applicant)
                # filter_expiry = Q(date_expiry__gte=today_local)
                filter_used = Q(date_used__isnull=True)
                site_fee_remainders = ApiarySiteFeeRemainder.objects.filter(
                    filter_site_category &
                    filter_site_fee_type &
                    filter_applicant &
                    filter_proxy_applicant &
                    # filter_expiry &
                    filter_used
                ).order_by('datetime_created')  # Older comes earlier

                filter_site_fee_type = Q(apiary_site_fee_type=ApiarySiteFeeType.objects.get(name=ApiarySiteFeeType.FEE_TYPE_RENEWAL))
                site_fee_remainders_renewal = ApiarySiteFeeRemainder.objects.filter(
                    filter_site_category &
                    filter_site_fee_type &
                    filter_applicant &
                    filter_proxy_applicant &
                    # filter_expiry &
                    filter_used
                ).order_by('datetime_created')  # Older comes earlier

                # Retrieve current fee
                site_category = SiteCategory.objects.get(name=category[0])
                fee = site_category.retrieve_fee_by_date_and_type(today_local, ApiarySiteFeeType.FEE_TYPE_APPLICATION)
                fee_renewal = site_category.retrieve_fee_by_date_and_type(today_local, ApiarySiteFeeType.FEE_TYPE_RENEWAL)

                remainder = {
                    'category_name': category[1],
                    'remainders': site_fee_remainders.count(),
                    'remainders_renewal': site_fee_remainders_renewal.count(),
                    'fee': fee,
                    'fee_renewal': fee_renewal,
                }
                ret_list.append(remainder)
            except:
                pass

        return ret_list

    def get_applicant_checklist_answers(self, obj):
        return ApiaryChecklistAnswerSerializer(
                obj.apiary_checklist.filter(question__checklist_role='applicant').order_by('question__order'),
                many=True).data

    def get_assessor_checklist_answers(self, obj):
        return ApiaryChecklistAnswerSerializer(
                obj.apiary_checklist.filter(question__checklist_role='assessor').filter(question__checklist_type='apiary').order_by('question__order'),
                many=True).data

    def _load_apiary_checklist_cache(self, obj):
        # Load and cache all related ApiaryChecklistAnswer instances for this
        # ProposalApiary to avoid issuing many DB queries during serialization.
        if not hasattr(self, "_apiary_checklist_cache"):
            try:
                qs = obj.apiary_checklist.select_related("question", "apiary_site", "apiary_referral").all()
                # Evaluate queryset and store as list for in-memory filtering
                self._apiary_checklist_cache = list(qs)
            except Exception:
                self._apiary_checklist_cache = []
        return self._apiary_checklist_cache

    def get_assessor_checklist_answers_per_site(self, obj):
        answers = [a for a in self._load_apiary_checklist_cache(obj)
                   if a.question.checklist_role == 'assessor' and a.question.checklist_type == 'apiary_per_site']
        # sort by question.order then id to preserve previous ordering
        answers.sort(key=lambda a: (getattr(a.question, 'order', 0), getattr(a, 'id', 0)))
        return ApiaryChecklistAnswerSerializer(answers, many=True).data

    def get_referrer_checklist_answers(self, obj):
        referral_list = []
        checklist = self._load_apiary_checklist_cache(obj)
        for referral in obj.proposal.referrals.all():
            answers = [a for a in checklist if a.apiary_referral_id == getattr(referral.apiary_referral, 'id', None) and a.question.checklist_type == 'apiary']
            answers.sort(key=lambda a: (getattr(a.question, 'order', 0), getattr(a, 'id', 0)))
            qs = ApiaryChecklistAnswerSerializer(answers, many=True).data
            referral_list.append({
                "referral_id": referral.id,
                "apiary_referral_id": referral.apiary_referral.id,
                "referral_data": qs,
                "referrer_group_name": referral.apiary_referral.referral_group.name,
            })
        return referral_list

    def get_referrer_checklist_answers_per_site(self, obj):
        referral_list = []
        checklist = self._load_apiary_checklist_cache(obj)
        for referral in obj.proposal.referrals.all():
            for site in obj.apiary_sites.all():
                answers = [a for a in checklist if a.apiary_referral_id == getattr(referral.apiary_referral, 'id', None) and a.question.checklist_type == 'apiary_per_site' and getattr(a.apiary_site, 'id', None) == getattr(site, 'id', None)]
                answers.sort(key=lambda a: (getattr(a.question, 'order', 0), getattr(a, 'id', 0)))
                qs = ApiaryChecklistAnswerSerializer(answers, many=True).data
                referral_list.append({
                    "referral_id": referral.id,
                    "apiary_referral_id": referral.apiary_referral.id,
                    "referral_data": qs,
                    "referrer_group_name": referral.apiary_referral.referral_group.name,
                })
        return referral_list

    def get_site_transfer_assessor_checklist_answers(self, obj):
        return ApiaryChecklistAnswerSerializer(
                obj.apiary_checklist.filter(question__checklist_role='assessor').filter(question__checklist_type='site_transfer').order_by('question__order'),
                many=True).data

    def get_site_transfer_assessor_checklist_answers_per_site(self, obj):
        answers = [a for a in self._load_apiary_checklist_cache(obj)
                   if a.question.checklist_role == 'assessor' and a.question.checklist_type == 'site_transfer_per_site']
        answers.sort(key=lambda a: (getattr(a.question, 'order', 0), getattr(a, 'id', 0)))
        return ApiaryChecklistAnswerSerializer(answers, many=True).data

    def get_site_transfer_referrer_checklist_answers(self, obj):
        referral_list = []
        for referral in obj.proposal.referrals.all():
            qs = ApiaryChecklistAnswerSerializer(
                obj.apiary_checklist.filter(apiary_referral_id=referral.apiary_referral.id).filter(question__checklist_type='site_transfer').order_by('question__order'),
                many=True).data
            referral_list.append({
                "referral_id": referral.id,
                "apiary_referral_id": referral.apiary_referral.id,
                "referral_data": qs,
                "referrer_group_name": referral.apiary_referral.referral_group.name,
                })
        return referral_list

    def get_site_transfer_referrer_checklist_answers_per_site(self, obj):
        referral_list = []
        checklist = self._load_apiary_checklist_cache(obj)
        for referral in obj.proposal.referrals.all():
            for site in obj.get_relations():
                answers = [a for a in checklist if a.apiary_referral_id == getattr(referral.apiary_referral, 'id', None) and a.question.checklist_type == 'site_transfer_per_site' and getattr(a.apiary_site, 'id', None) == getattr(site.apiary_site, 'id', None)]
                answers.sort(key=lambda a: (getattr(a.question, 'order', 0), getattr(a, 'id', 0)))
                qs = ApiaryChecklistAnswerSerializer(answers, many=True).data
                referral_list.append({
                    "referral_id": referral.id,
                    "apiary_referral_id": referral.apiary_referral.id,
                    "referral_data": qs,
                    "referrer_group_name": referral.apiary_referral.referral_group.name,
                })
        return referral_list


class CreateProposalApiarySiteTransferSerializer(serializers.ModelSerializer):
    proposal_id = serializers.IntegerField(
            required=True, write_only=True, allow_null=False)
    originating_approval_id = serializers.IntegerField(
            required=True, write_only=True, allow_null=False)

    class Meta:
        model = ProposalApiary

        fields = (
            'id',
            'title',
            'proposal_id',
            'originating_approval_id',
            'longitude',
            'latitude',
        )
        read_only_fields = (
            'id',
        )


class SaveProposalApiarySerializer(serializers.ModelSerializer):
    proposal_id = serializers.IntegerField(
            required=True, write_only=True, allow_null=False)

    class Meta:
        model = ProposalApiary

        fields = (
            'id',
            'title',
            'proposal_id',
            'longitude',
            'latitude',
        )
        read_only_fields = (
                'id',
                )


class TemporaryUseApiarySiteSerializer(serializers.ModelSerializer):
    proposal_apiary_temporary_use_id = serializers.IntegerField(write_only=True, required=False)
    apiary_site_on_approval_id = serializers.IntegerField(write_only=True, required=False)
    apiary_site = serializers.SerializerMethodField()

    def get_apiary_site(self, obj):
        return ApiarySiteOnApprovalGeometrySerializer(obj.apiary_site_on_approval).data

    def validate(self, attrs):
        #TODO on cleanup (old comment) check if the site is not temporary used to another person for the period
        #TODO on cleanup (old comment) check if the licence is valid, etc
        return attrs

    class Meta:
        model = TemporaryUseApiarySite
        fields = (
            'id',
            'proposal_apiary_temporary_use_id',
            'apiary_site_on_approval_id',
            'apiary_site',
            # 'apiary_site_on_approval',
            # 'apiary_site_approval_id',
            # 'apiary_site_id',
            # 'apiary_site',
            'selected',
        )


class ProposalApiaryTemporaryUseSerializer(serializers.ModelSerializer):
    proposal_id = serializers.IntegerField(required=False)
    loaning_approval_id = serializers.IntegerField(required=False)
    deed_poll_documents = serializers.SerializerMethodField()
    lodgement_number = serializers.CharField(source='proposal.lodgement_number', required=False, read_only=True)
    customer_status = serializers.SerializerMethodField()
    processing_status = serializers.SerializerMethodField()
    temporary_use_apiary_sites = TemporaryUseApiarySiteSerializer(many=True, read_only=True)

    def validate(self, data):
        if hasattr(self, 'context') and self.context and self.context['action'] == 'submit':
            # When this proposal is submitted, it should be validated
            field_errors = {}
            non_field_errors = []

            if not data['from_date']:
                field_errors['Period From'] = 'This field is required'
            if not data['to_date']:
                field_errors['Period To'] = 'This field is required'
            if not data['temporary_occupier_name']:
                field_errors['Temporary Occupier Name'] = 'This field is required'

            # if data['issued_on_paper']:
            #     if not data['paper_id']:
            #         non_field_errors.append('Paper ID is required')
            #     if not data['date_of_issue']:
            #         non_field_errors.append('Date of Issue is required')
            #     if not data['time_of_issue']:
            #         non_field_errors.append('Time of Issue is required')
            #     if not self.context['num_of_documents_attached']:
            #         non_field_errors.append('Paper notice is required')
            #     if not data['offender_id']:
                    # non_field_errors.append('Offender is required')

            if field_errors:
                raise serializers.ValidationError(field_errors)

            if non_field_errors:
                raise serializers.ValidationError(non_field_errors)

        return data

    def get_processing_status(self, obj):
        status = obj.proposal.processing_status
        ret = ''
        for id, value in Proposal.PROCESSING_STATUS_CHOICES:
            if id == status:
                ret = value
                break
        return ret

    def get_customer_status(self, obj):
        status = obj.proposal.customer_status
        ret = ''
        for id, value in Proposal.CUSTOMER_STATUS_CHOICES:
            if id == status:
                ret = value
                break
        return ret

    def get_deed_poll_documents(self, obj):
        url_list = []

        if obj.proposal.deed_poll_documents.all().count():
            for doc in obj.proposal.deed_poll_documents.all():
                #if self.context.get('internal', False):
                #    # count_logs = doc.access_logs.count()
                #    url = '<a href="{}" target="_blank">{}</a>'.format(doc._file.url, doc.name) + viewed_text
                #else:
                #    # To detect if the external user accessing the pdf file, we make Django serve the pdf file
                #    url = '<a href="/api/sanction_outcome/{}/doc?name={}" target="_blank">{}</a>'.format(obj.id, doc.name, doc.name)
                url = f'<a href="{doc._file.url}" target="_blank">{doc.name}</a>'
                url_list.append(url)

        urls = '<br />'.join(url_list)
        return urls

    class Meta:
        model = ProposalApiaryTemporaryUse
        fields = (
            'id',
            'from_date',
            'to_date',
            'temporary_occupier_name',
            'temporary_occupier_phone',
            'temporary_occupier_mobile',
            'temporary_occupier_email',
            'proposal_id',
            'loaning_approval_id',
            'deed_poll_documents',
            'lodgement_number',
            'customer_status',
            'processing_status',
            'temporary_use_apiary_sites',
        )


#class ProposalApiarySiteTransferSerializer(serializers.ModelSerializer):
#
#    class Meta:
#        model = ProposalApiarySiteTransfer
#        fields = '__all__'


class SiteCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SiteCategory
        fields = '__all__'


class ApiarySiteFeeTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ApiarySiteFeeType
        fields = '__all__'


class ApiarySiteFeeSerializer(serializers.ModelSerializer):
    site_category = SiteCategorySerializer()
    apiary_site_fee_type = ApiarySiteFeeTypeSerializer()

    class Meta:
        model = ApiarySiteFee
        fields = (
                'site_category',
                'apiary_site_fee_type',
                'amount',
                'date_of_enforcement',
                )


class ProposalApiaryDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalApiaryDocument
        fields = ('id', 'name', '_file')


class ProposalApiaryTypeSerializer(serializers.ModelSerializer):
    readonly = serializers.SerializerMethodField(read_only=True)
    documents_url = serializers.SerializerMethodField()
    proposal_type = serializers.SerializerMethodField()
    get_history = serializers.ReadOnlyField()
    fee_invoice_url = serializers.SerializerMethodField()

    submitter = serializers.CharField(source='submitter.get_full_name')
    processing_status = serializers.SerializerMethodField(read_only=True)
    review_status = serializers.SerializerMethodField(read_only=True)
    customer_status = serializers.SerializerMethodField(read_only=True)

    application_type = serializers.CharField(source='application_type.name', read_only=True)
    proposal_apiary = ProposalApiarySerializer()
    apiary_temporary_use = ProposalApiaryTemporaryUseSerializer(many=False, read_only=True)
    #apiary_site_transfer = ProposalApiarySiteTransferSerializer()
    apiary_group_application_type = serializers.SerializerMethodField()
    is_internal_user = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = (
                'id',
                'application_type',
                'proposal_type',
                'title',
                'customer_status',
                'processing_status',
                'review_status',
                #'applicant_type',
                'applicant',
                #'org_applicant',
                #'proxy_applicant',
                'submitter',
                'assigned_officer',
                'previous_application',
                'get_history',
                'lodgement_date',
                'modified_date',
                'documents',
                'requirements',
                'readonly',
                'can_user_edit',
                'can_user_view',
                'documents_url',
                'reference',
                'lodgement_number',
                'lodgement_sequence',
                'can_officer_process',
                'proposal_type',
                #'pending_amendment_request',
                #'is_amendment_proposal',

                #'applicant_details',
                #'training_completed',
                'fee_invoice_url',
                # 'fee_invoice_reference',
                'fee_invoice_references',
                'fee_paid',
                'activity',
                'proposal_apiary',
                'apiary_temporary_use',
                #'apiary_site_transfer',
                'apiary_group_application_type',
                'is_internal_user',

                )
        read_only_fields=('documents',)

    def get_documents_url(self,obj):
        return f'/private-media/{settings.MEDIA_APP_DIR}/proposals/{obj.id}/documents/'

    def get_readonly(self,obj):
        return obj.can_user_view
        #return False

    def get_processing_status(self,obj):
        return obj.get_processing_status_display()

    def get_review_status(self,obj):
        return obj.get_review_status_display()

    def get_customer_status(self,obj):
        return obj.get_customer_status_display()

    def get_proposal_type(self,obj):
        return obj.get_proposal_type_display()

    def get_fee_invoice_url(self,obj):
        # return '/payments/invoice-pdf/{}'.format(obj.fee_invoice_reference) if obj.fee_paid else None
        ret_list = []
        if obj.fee_invoice_references:
            for ref in obj.fee_invoice_references:
                ret_list.append(f'payments/invoice-pdf/{ref}')
        return ret_list

    def get_apiary_group_application_type(self, obj):
        return obj.apiary_group_application_type

    def get_is_internal_user(self, obj):
        try:
            request = self.context.get('request')
            return is_internal(request)
        except:
            return False


class ApiaryReferralGroupSerializer(serializers.ModelSerializer):
    all_members_list = serializers.SerializerMethodField()
    class Meta:
        model = ApiaryReferralGroup
        fields = (
                'id',
                'name',
                'all_members_list',
                )

    def get_all_members_list(self, obj):
        serializer = EmailUserSerializer(obj.all_members, many=True)
        return serializer.data


class ApiaryProposalReferralSerializer(serializers.ModelSerializer):
    referral = serializers.SerializerMethodField()
    processing_status = serializers.CharField(source='get_processing_status_display')
    apiary_referral = serializers.SerializerMethodField()
    class Meta:
        model = Referral
        fields = '__all__'

    def get_apiary_referral(self, obj):
        return ApiaryReferralSerializer(obj.apiary_referral).data

    #TODO on-cleanup: this was added as a fix but this column may not be needed for apiary
    def get_referral(self, obj):
        return obj.referral.get_full_name() if obj.referral else None

class ApiaryInternalApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Approval
        fields = (
                'id',
                'lodgement_number',
                'start_date',
                'expiry_date',
                'reissued',
                )

# matches InternalProposalSerializer for apiary group proposals
class ApiaryInternalProposalSerializer(BaseProposalSerializer):
    processing_status = serializers.SerializerMethodField(read_only=True)
    review_status = serializers.SerializerMethodField(read_only=True)
    customer_status = serializers.SerializerMethodField(read_only=True)
    submitter = serializers.CharField(source='submitter.get_full_name')
    submitter_email = serializers.CharField(source='submitter.email')
    proposaldeclineddetails = ProposalDeclinedDetailsSerializer()
    assessor_mode = serializers.SerializerMethodField()
    current_assessor = serializers.SerializerMethodField()
    assessor_data = serializers.SerializerMethodField()
    latest_referrals = ApiaryProposalReferralSerializer(many=True)
    allowed_assessors = EmailUserSerializer(many=True)
    approval_level_document = serializers.SerializerMethodField()
    application_type = serializers.CharField(source='application_type.name', read_only=True)
    fee_invoice_url = serializers.SerializerMethodField()
    applicant = serializers.SerializerMethodField()
    applicant_type = serializers.SerializerMethodField()
    applicant_address = serializers.SerializerMethodField()
    applicant_first_name = serializers.SerializerMethodField()
    applicant_last_name = serializers.SerializerMethodField()
    applicant_phone_number = serializers.SerializerMethodField()
    applicant_mobile_number = serializers.SerializerMethodField()
    applicant_email = serializers.SerializerMethodField()

    proposal_apiary = ProposalApiarySerializer()

    apiary_temporary_use = ProposalApiaryTemporaryUseSerializer(many=False, read_only=True)

    #apiary_site_transfer = ProposalApiarySiteTransferSerializer()

    applicant_checklist = serializers.SerializerMethodField()
    apiary_group_application_type = serializers.SerializerMethodField()
    # approval = ApiaryInternalApprovalSerializer()
    approval = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = (
                'id',
                'application_type',
                'activity',
                'approval_level',
                'approval_level_document',
                #'region',
                #'district',
                'title',
                'data',
                #'schema',
                'customer_status',
                'processing_status',
                'review_status',
                #applicant',
                #'org_applicant',
                #'proxy_applicant',
                'submitter',
                'submitter_email',
                #'applicant_type',
                'assigned_officer',
                'assigned_approver',
                'previous_application',
                'get_history',
                'lodgement_date',
                'modified_date',
                'documents',
                'requirements',
                'readonly',
                'can_user_edit',
                'can_user_view',
                'documents_url',
                'assessor_mode',
                'current_assessor',
                'assessor_data',
                'comment_data',
                'latest_referrals',
                'allowed_assessors',
                'proposed_issuance_approval',
                'proposed_decline_status',
                'proposaldeclineddetails',
                'permit',
                'reference',
                'lodgement_number',
                'lodgement_sequence',
                'can_officer_process',
                'proposal_type',
                # tab field models
                #'applicant_details',
                #'assessor_assessment',
                #'referral_assessments',
                # 'fee_invoice_reference',
                'fee_invoice_references',
                'fee_invoice_url',
                'fee_paid',
                'applicant',
                'applicant_type',
                'proposal_apiary',
                'apiary_temporary_use',
                #'apiary_site_transfer',
                'applicant_address',

                # 'apiary_checklist',
                'applicant_checklist',
                'applicant_address',
                'applicant_first_name',
                'applicant_last_name',
                'applicant_phone_number',
                'applicant_mobile_number',
                'applicant_email',
                'apiary_group_application_type',
                'approval',
                )
        read_only_fields=('documents','requirements')

    def get_approval(self, proposal):
        ret_appr = None
        if hasattr(proposal, 'proposal_apiary') and proposal.proposal_apiary:
            appr = proposal.proposal_apiary.retrieve_approval
            if appr:
                 ret_appr = ApiaryInternalApprovalSerializer(appr).data
        return ret_appr

    def get_apiary_group_application_type(self, obj):
        return obj.apiary_group_application_type

    def get_applicant_checklist(self, obj):
        if not hasattr(obj, 'proposal_apiary') or not obj.proposal_apiary:
            return []
        qs = obj.proposal_apiary.apiary_checklist.select_related('question').order_by('question__order')
        return ApiaryChecklistAnswerSerializer(qs, many=True).data

    def get_applicant_address(self, obj):
        if obj.relevant_applicant_address:
            return obj.relevant_applicant_address
        return None

    def get_applicant_first_name(self, obj):
        if obj.relevant_applicant and not obj.applicant:
            return obj.relevant_applicant.first_name

    def get_applicant_last_name(self, obj):
        if obj.relevant_applicant and not obj.applicant:
            return obj.relevant_applicant.last_name

    def get_applicant_phone_number(self, obj):
        if obj.relevant_applicant and not obj.applicant:
            return obj.relevant_applicant.phone_number

    def get_applicant_mobile_number(self, obj):
        if obj.relevant_applicant and not obj.applicant:
            return obj.relevant_applicant.mobile_number

    def get_applicant_email(self, obj):
        if obj.relevant_applicant and not obj.applicant:
            return obj.relevant_applicant.email

    def get_approval_level_document(self,obj):
        if obj.approval_level_document is not None:
            return [obj.approval_level_document.name,obj.approval_level_document._file.url]
        else:
            return obj.approval_level_document

    def get_assessor_mode(self,obj):
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        return {
            'assessor_mode': True,
            'has_assessor_mode': obj.has_assessor_mode(user),
            'assessor_can_assess': obj.can_assess(user),
            'assessor_level': 'assessor',
            'assessor_box_view': obj.assessor_comments_view(user)
        }

    def get_can_edit_activities(self,obj):
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        return obj.can_edit_activities(user)

    def get_readonly(self,obj):
        return True

    def get_current_assessor(self,obj):
        return {
            'id': self.context['request'].user.id,
            'name': self.context['request'].user.get_full_name(),
            'email': self.context['request'].user.email
        }

    def get_assessor_data(self,obj):
        return obj.assessor_data

    def get_reversion_ids(self,obj):
        return obj.reversion_ids[:5]

    def get_fee_invoice_url(self,obj):
        # return '/payments/invoice-pdf/{}'.format(obj.fee_invoice_reference) if obj.fee_paid else None
        ret_list = []
        if obj.fee_invoice_references:
            for ref in obj.fee_invoice_references:
                ret_list.append(f'payments/invoice-pdf/{ref}')
        return ret_list

    def get_applicant(self,obj):
        serializer = None
        if obj.relevant_applicant_type == 'organisation':
            serializer = OrganisationSerializer(obj.relevant_applicant)
        else:
            serializer = EmailUserSerializer(obj.relevant_applicant)
        return serializer.data

    def get_applicant_type(self,obj):
        return obj.relevant_applicant_type


class ApiaryReferralSerializer(serializers.ModelSerializer):
    #processing_status = serializers.CharField(source='get_processing_status_display')
    #latest_referrals = ProposalReferralSerializer(many=True)
    can_process = serializers.BooleanField()
    can_assign = serializers.BooleanField()
    referral_group = ApiaryReferralGroupSerializer()
    allowed_assessors = EmailUserSerializer(many=True)
    assigned_officer = EmailUserSerializer()
    current_officer = serializers.SerializerMethodField()
    class Meta:
        model = ApiaryReferral
        fields = (
                'id',
                'referral_group',
                'can_process',
                'can_assign',
                'allowed_assessors',
                'current_officer',
                'assigned_officer',
                'assigned_officer_id',
                )

    def get_current_officer(self, obj):
        request = self.context.get('request')
        if request:
            return {
                    'id': request.user.id,
                    'name': request.user.get_full_name(),
                    'email': request.user.email,
                    }

    #def __init__(self,*args,**kwargs):
     #   super(ReferralSerializer, self).__init__(*args, **kwargs)
      #  self.fields['proposal'] = ReferralProposalSerializer(context={'request':self.context['request']})


class FullApiaryReferralSerializer(serializers.ModelSerializer):
    processing_status = serializers.CharField(source='get_processing_status_display')
    latest_referrals = ApiaryProposalReferralSerializer(many=True)
    can_be_completed = serializers.BooleanField()
    apiary_referral = ApiaryReferralSerializer()
    class Meta:
        model = Referral
        fields = '__all__'

    def __init__(self,*args,**kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proposal'] = ApiaryReferralProposalSerializer(context={'request':self.context['request']})


class ApiaryReferralProposalSerializer(ApiaryInternalProposalSerializer):
    def get_assessor_mode(self,obj):
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        try:
            referral = Referral.objects.get(proposal=obj,referral=user)
        except:
            referral = None
        return {
            'assessor_mode': True,
            'assessor_can_assess': referral.can_assess_referral(user) if referral else None,
            'assessor_level': 'referral',
            'assessor_box_view': obj.assessor_comments_view(user)
        }


class SendApiaryReferralSerializer(serializers.Serializer):
    #email = serializers.EmailField()
    group_id = serializers.IntegerField()
    text = serializers.CharField(allow_blank=True)


class DTApiaryReferralSerializer(serializers.ModelSerializer):
    processing_status = serializers.CharField(source='proposal.get_processing_status_display')
    referral_status = serializers.CharField(source='get_processing_status_display')
    proposal_lodgement_date = serializers.CharField(source='proposal.lodgement_date')
    proposal_lodgement_number = serializers.CharField(source='proposal.lodgement_number')
    submitter = serializers.SerializerMethodField()
    region = serializers.CharField(source='region.name', read_only=True)
    #referral = EmailUserSerializer()
    apiary_referral = ApiaryReferralSerializer()
    class Meta:
        model = Referral
        fields = (
            'id',
            'region',
            'activity',
            'title',
            'applicant',
            'submitter',
            'processing_status',
            'referral_status',
            'lodged_on',
            'proposal',
            'can_be_processed',
            'referral',
            'proposal_lodgement_date',
            'proposal_lodgement_number',
            'referral_text',
            'apiary_referral',
        )

    def get_submitter(self,obj):
        return EmailUserSerializer(obj.proposal.submitter).data


class UserApiaryApprovalSerializer(serializers.ModelSerializer):
    licence_holders = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = EmailUser
        fields = (
                'id',
                'licence_holders',
                )

    def get_licence_holders(self, obj):
        originating_approval_id = self.context.get('originating_approval_id')
        #return 'apiary_approvals'
        licence_holders = []
        #multiple_approvals = False
        #individual_approvals = False
        #organisation_approvals = False
        #Individual applications
        for individual_approval in obj.disturbance_proxy_approvals.filter(
                status='current',
                apiary_approval=True
                ).exclude(id=originating_approval_id
                        ):
            #approval = Approval.objects.filter(applicant=self.proposal.applicant, status='current', apiary_approval=True).first()
            if individual_approval.apiary_approval:
                licence_holders.append({
                    'type': 'individual',
                    'id':individual_approval.id,
                    'lodgement_number':individual_approval.lodgement_number,
                    'licence_holder': individual_approval.relevant_applicant_name,
                    })
                #individual_approvals = True
        # add user if no licence exists
        if not licence_holders:
            licence_holders.append({
                'type': 'individual',
                'id': None,
                'lodgement_number': None,
                'licence_holder': obj.get_full_name(),
                'transferee_id': obj.id,
                })
        #Organisation applications
        user_delegations = UserDelegation.objects.filter(user=obj)
        #organisation_approvals = []
        for user_delegation in user_delegations:
            #organisation_approvals.append(user_delegation.organisation.disturbance_approvals.all())
            # add org even if no licence exists
            if not user_delegation.organisation.disturbance_approvals.filter(
                    status='current',
                    apiary_approval=True
                    ).exclude(id=originating_approval_id
                            ):
                licence_holders.append({
                    'type': 'organisation',
                    'id': None,
                    'lodgement_number':None,
                    'licence_holder': user_delegation.organisation.name,
                    'transferee_id': obj.id,
                    'organisation_id': user_delegation.organisation.id,
                    })
            else:
                # licence exists
                for organisation_approval in user_delegation.organisation.disturbance_approvals.filter(
                        status='current',
                        apiary_approval=True
                        ).exclude(id=originating_approval_id
                                ):
                    if organisation_approval.apiary_approval:
                        licence_holders.append({
                            'type': 'organisation',
                            'id':organisation_approval.id,
                            'lodgement_number':organisation_approval.lodgement_number,
                            'licence_holder': organisation_approval.relevant_applicant_name,
                            })
                        #organisation_approvals = True
            #approvals.append(organisation_approvals)

        #if individual_approvals and organisation_approvals:
         #   multiple_approvals = True

        #return {'approvals': approvals, 'multiple': multiple_approvals}
        return {'licence_holders': licence_holders}


class ApiaryProposalRequirementSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField(input_formats=['%d/%m/%Y'],required=False,allow_null=True)
    class Meta:
        model = ProposalRequirement
        fields = ('id','due_date','free_requirement','standard_requirement','standard','order','proposal','recurrence','recurrence_schedule','recurrence_pattern','requirement','is_deleted','copied_from')
        read_only_fields = ('order','requirement', 'copied_from')

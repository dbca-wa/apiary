from django.conf import settings
from ledger_api_client.ledger_models import EmailUserRO as EmailUser,Address, Document
from disturbance.components.organisations.models import (   
                                    Organisation,
                                )
from disturbance.components.organisations.utils import can_admin_org, is_consultant
from rest_framework import serializers
from disturbance.components.approvals.models import Approval
from disturbance.components.proposals.models import Proposal
from disturbance.components.main.models import ApplicationType
from disturbance.helpers import is_internal

class DocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        fields = ('id','description','file','name','uploaded_date')

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            'id',
            'line1',
            'locality',
            'state',
            'country',
            'postcode'
        ) 

class UserOrganisationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='organisation.organisation_name')
    abn = serializers.CharField(source='organisation.organisation_abn')
    is_consultant = serializers.SerializerMethodField(read_only=True)
    is_admin = serializers.SerializerMethodField(read_only=True)
    current_apiary_approval = serializers.SerializerMethodField(read_only=True) # includes current & suspended
    existing_record_text = serializers.SerializerMethodField()

    class Meta:
        model = Organisation
        fields = (
            'id',
            'name',
            'abn',
            'email',
            'is_consultant',
            'is_admin',
            'current_apiary_approval',
            'existing_record_text',
        )

    def get_current_apiary_approval(self, obj):
        approval = obj.disturbance_approvals.filter(status__in=[Approval.STATUS_CURRENT, Approval.STATUS_SUSPENDED], apiary_approval=True).first()
        if approval:
            return approval.id

    def get_existing_record_text(self, obj):
        notification = ''
        disable_radio_button = False

        request = self.context.get('request')

        approval = obj.disturbance_approvals.filter(status__in=[Approval.STATUS_CURRENT, Approval.STATUS_SUSPENDED], apiary_approval=True).first()
        open_proposal = None
        # Apiary group applications
        for proposal in Proposal.objects.filter(applicant=obj, application_type__name__in=[
            ApplicationType.APIARY,
            ApplicationType.TEMPORARY_USE,
            ApplicationType.SITE_TRANSFER,
            ]):
            if not proposal.processing_status in [
                    Proposal.PROCESSING_STATUS_APPROVED, 
                    Proposal.PROCESSING_STATUS_DECLINED, 
                    Proposal.PROCESSING_STATUS_DISCARDED
                    ]:
                open_proposal = proposal
        # Any open Apiary proposal will block the user from opening a new Apiary/Site Transfer/Temporary Use application
        if open_proposal:
            disable_radio_button = True
            notification = '<span class="proposalWarning">  (Application {} in progress)</span>'.format(open_proposal.lodgement_number)
        elif approval:
            notification = '<span>  (Make changes to Licence {})</span>'.format(approval.lodgement_number)

        return {
                "disable_radio_button": disable_radio_button,
                "notification": notification,
                }

    def get_is_admin(self, obj):
        user = EmailUser.objects.get(id=self.context.get('user_id'))
        return can_admin_org(obj, user)

    def get_is_consultant(self, obj):
        user = EmailUser.objects.get(id=self.context.get('user_id'))
        return is_consultant(obj, user)

    def get_email(self, obj):
        email = EmailUser.objects.get(id=self.context.get('user_id')).email
        return email

class UserFilterSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = EmailUser
        fields = (
            'id',
            'last_name',
            'first_name',
            'email',
            'name'
        )

    def get_name(self, obj):
        return obj.get_full_name()


class UserSerializer(serializers.ModelSerializer):
    disturbance_organisations = serializers.SerializerMethodField()
    residential_address = UserAddressSerializer()
    personal_details = serializers.SerializerMethodField()
    address_details = serializers.SerializerMethodField()
    contact_details = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    current_apiary_approval = serializers.SerializerMethodField()
    existing_record_text = serializers.SerializerMethodField()
    is_internal = serializers.SerializerMethodField()

    class Meta:
        model = EmailUser
        fields = (
            'id',
            'last_name',
            'first_name',
            'email',
            'residential_address',
            'phone_number',
            'mobile_number',
            'disturbance_organisations',
            'personal_details',
            'address_details',
            'contact_details',
            'full_name',
            'current_apiary_approval',
            'existing_record_text',
            'is_internal',
        )

    def get_is_internal(self, obj):
        request = self.context.get('request')
        return is_internal(request)

    def get_current_apiary_approval(self, obj):
        approval = obj.disturbance_proxy_approvals.filter(status__in=[Approval.STATUS_CURRENT, Approval.STATUS_SUSPENDED], apiary_approval=True).first()
        if approval:
            return approval.id

    def get_existing_record_text(self, obj):
        notification = ''
        disable_radio_button = False

        request = self.context.get('request')

        approval = obj.disturbance_proxy_approvals.filter(status__in=[Approval.STATUS_CURRENT, Approval.STATUS_SUSPENDED], apiary_approval=True).first()
        open_proposal = None
        # Apiary group applications
        for proposal in Proposal.objects.filter(proxy_applicant=obj, application_type__name__in=[
            ApplicationType.APIARY,
            ApplicationType.TEMPORARY_USE,
            ApplicationType.SITE_TRANSFER,
            ]):
            if not proposal.processing_status in [
                    Proposal.PROCESSING_STATUS_APPROVED, 
                    Proposal.PROCESSING_STATUS_DECLINED, 
                    Proposal.PROCESSING_STATUS_DISCARDED
                    ]:
                open_proposal = proposal
        # Any open proposal will block the user from opening a new Apiary/Site Transfer/Temporary Use application
        if open_proposal:
            disable_radio_button = True
            notification = '<span class="proposalWarning">  (Application {} in progress)</span>'.format(open_proposal.lodgement_number)
        elif approval:
            notification = '<span>  (Make changes to Licence {})</span>'.format(approval.lodgement_number)

        return {
                "disable_radio_button": disable_radio_button,
                "notification": notification,
                }

    def get_personal_details(self,obj):
        return True if obj.last_name  and obj.first_name else False

    def get_address_details(self,obj):
        return True if obj.residential_address else False

    def get_contact_details(self,obj):
        if obj.mobile_number and obj.email:
            return True
        elif obj.email and obj.phone_number:
            return True
        else:
            return False

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_disturbance_organisations(self, obj):
        request = self.context.get('request')
        disturbance_organisations = obj.disturbance_organisations
        serialized_orgs = UserOrganisationSerializer(
            disturbance_organisations, many=True, 
            context={
                'user_id': obj.id,
                'request': request
                }).data
        return serialized_orgs


class PersonalSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        fields = (
            'id',
            'last_name',
            'first_name',
        )

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        fields = (
            'id',
            'email',
            'phone_number',
            'mobile_number',
        )

    def validate(self, obj):
        if not obj.get('phone_number') and not obj.get('mobile_number'):
            raise serializers.ValidationError('You must provide a mobile/phone number')
        return obj

class MyUserDetailsSerializer(serializers.ModelSerializer):
    residential_address = UserAddressSerializer()
    personal_details = serializers.SerializerMethodField()
    address_details = serializers.SerializerMethodField()
    contact_details = serializers.SerializerMethodField()
    disturbance_organisations = serializers.SerializerMethodField()
    #identification = IdentificationSerializer()
    is_customer = serializers.SerializerMethodField()
    is_internal = serializers.SerializerMethodField()
    dob = serializers.SerializerMethodField(read_only=True)
    legal_dob = serializers.SerializerMethodField(read_only=True)
    #has_complete_first_time = serializers.SerializerMethodField(read_only=True)
    sso_setting_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EmailUser
        fields = (
            'title',
            'id',
            'last_name',
            'first_name',
            'dob',
            'legal_last_name',
            'legal_first_name',
            'legal_dob',
            'email',
            # 'identification',
            'residential_address',
            'phone_number',
            'mobile_number',
            'fax_number',
            'disturbance_organisations',
            'personal_details',
            'address_details',
            'contact_details',
            'is_customer',
            'is_internal',
            'sso_setting_url',
        )

    def get_has_complete_first_time(self, obj):
        '''
        Verify request user has completed adding reqired details for first time
        usage.
        '''
        is_completed = False

        request = self.context.get('request')

        if is_internal(request):
            is_completed = True
        else:
            is_completed = not is_new_to_wildlifelicensing(request)

        return is_completed


    def get_dob(self, obj):
        formatted_date = obj.dob.strftime(
            '%d/%m/%Y'
        ) if obj.dob else None

        return formatted_date
    
    def get_legal_dob(self, obj):
        formatted_date = obj.legal_dob.strftime(
            '%d/%m/%Y'
        ) if obj.legal_dob else None

        return formatted_date

    def get_personal_details(self, obj):
        return True if obj.last_name and obj.first_name and (obj.dob or obj.legal_dob)  else False

    def get_address_details(self, obj):
        return True if obj.residential_address else False

    def get_contact_details(self, obj):
        if obj.mobile_number and obj.email:
            return True
        elif obj.phone_number and obj.email:
            return True
        elif obj.mobile_number and obj.phone_number:
            return True
        else:
            return False

    def get_disturbance_organisations(self, obj):
        request = self.context.get('request')
        disturbance_organisations = obj.disturbance_organisations
        serialized_orgs = UserOrganisationSerializer(
            disturbance_organisations, many=True, 
            context={
                'user_id': obj.id,
                'request': request
                }).data
        return serialized_orgs

    def get_is_customer(self, obj):
        return not is_internal(self.context.get('request'))

    def get_is_internal(self, obj):
        return is_internal(self.context.get('request'))
    
    def get_sso_setting_url(self, obj):
        return settings.SSO_SETTING_URL
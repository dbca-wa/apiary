import logging

from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import JSONField, Q
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from ledger_api_client.utils import create_organisation, get_search_organisation
from rest_framework import serializers, status
from six import python_2_unicode_compatible

from disturbance.components.main.models import (
    CommunicationsLogEntry,
    LedgerDocument,
    SanitiseFileMixin,
    SanitiseMixin,
    UserAction,
)
from disturbance.components.organisations.utils import random_generator

logger = logging.getLogger(__name__)
from disturbance.components.main.models import private_storage
from disturbance.components.main.utils import (
    get_first_name,
    get_last_name,
)
from disturbance.components.organisations.emails import (
    send_org_access_group_request_accept_email_notification,
    send_organisation_contact_adminuser_email_notification,
    send_organisation_contact_consultant_email_notification,
    send_organisation_contact_decline_email_notification,
    send_organisation_contact_suspend_email_notification,
    send_organisation_contact_user_email_notification,
    send_organisation_link_email_notification,
    send_organisation_reinstate_email_notification,
    send_organisation_request_accept_email_notification,
    send_organisation_request_decline_email_notification,
    send_organisation_request_email_notification,
    send_organisation_request_link_email_notification,
    send_organisation_unlink_email_notification,
)


@python_2_unicode_compatible
class Organisation(models.Model):
    organisation_id = models.IntegerField(unique=True, verbose_name="Ledger Organisation ID")
    delegates = models.ManyToManyField(
        EmailUser, blank=True, through="UserDelegation", related_name="disturbance_organisations"
    )
    admin_pin_one = models.CharField(max_length=50, blank=True)
    admin_pin_two = models.CharField(max_length=50, blank=True)
    user_pin_one = models.CharField(max_length=50, blank=True)
    user_pin_two = models.CharField(max_length=50, blank=True)

    # Property Caches to store Org Name and ABN without having to constantly query ledger - update on save or via management command - use for filtering
    # NOTE: this is a temporary solution for until we are able to fully migrate ledger organisation tables
    property_cache = JSONField(null=True, blank=True, default=dict)

    class Meta:
        app_label = "disturbance"

    def update_property_cache(self, save=True):

        # Update Cache
        self.property_cache["name"] = self.name
        self.property_cache["abn"] = self.abn

        if save is True:
            self.save()

        return self.property_cache

    def save(self, *args, **kwargs):
        if self.pk:
            self.update_property_cache(
                False
            )  # NOTE: very important that this is False to prevent an infinite save loop
        super().save(*args, **kwargs)

    @property
    def organisation(self):
        try:
            from disturbance.helpers import get_cached_ledger_organisation

            data = get_cached_ledger_organisation(self.organisation_id)
            if not data:
                logger.warning(
                    "Ledger API returned empty data for organisation_id=%s. The organisation may not exist in the ledger database.",
                    self.organisation_id,
                )

            return data
        except Exception as e:
            logger.error(
                "Failed to fetch organisation data for organisation_id=%s: %s",
                self.organisation_id,
                e,
            )
            raise ValidationError("Organisation does not exist")

    def __str__(self):
        return_str = ""

        if "name" in self.property_cache:
            return_str = self.property_cache["name"]
        if "abn" in self.property_cache:
            return_str += f" (ABN: {self.property_cache['abn']})"

        if not return_str:
            return str(f"{self.name} (ABN: {self.abn})")

        return return_str

    def log_user_action(self, action, request):
        return OrganisationAction.log_action(self, action, request.user)

    def validate_pins(self, pin1, pin2, request):
        try:
            val_admin = self.admin_pin_one == pin1 and self.admin_pin_two == pin2
            val_user = self.user_pin_one == pin1 and self.user_pin_two == pin2
            if val_admin:
                val = val_admin
                admin_flag = True
                role = "organisation_admin"
            elif val_user:
                val = val_user
                admin_flag = False
                role = "organisation_user"
            else:
                val = False
                return val

            self.add_user_contact(request.user, request, admin_flag, role)
            return val
        except Exception:
            return None

    def check_user_contact(self, request, admin_flag, role):
        user = request.user
        try:
            org = OrganisationContact.objects.create(
                organisation=self,
                first_name=user.first_name,
                last_name=user.last_name,
                mobile_number=user.mobile_number,
                phone_number=user.phone_number,
                fax_number=user.fax_number,
                email=user.email,
                user_role=role,
                user_status="pending",
                is_admin=admin_flag,
            )
            return org
        except Exception:
            return False

    def add_user_contact(self, user, request, admin_flag, role):
        with transaction.atomic():
            contact, created = OrganisationContact.objects.get_or_create(
                organisation=self,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                defaults={
                    "mobile_number": user.mobile_number,
                    "phone_number": user.phone_number,
                    "fax_number": user.fax_number,
                    "user_role": role,
                    "user_status": "pending",
                    "is_admin": admin_flag,
                },
            )

            if not created:
                contact.mobile_number = user.mobile_number
                contact.phone_number = user.phone_number
                contact.fax_number = user.fax_number
                contact.user_role = role
                contact.user_status = "pending"
                contact.is_admin = admin_flag
                contact.save()

            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_CONTACT_ADDED.format(f"{user.first_name} {user.last_name}({user.email})"),
                request,
            )

    def update_organisation(self, request):
        with transaction.atomic():
            self.log_user_action(OrganisationAction.ACTION_UPDATE_ORGANISATION, request)

    def update_address(self, request):
        self.log_user_action(OrganisationAction.ACTION_UPDATE_ADDRESS, request)

    def update_contacts(self, request):
        try:
            contact = self.contact.last()
            self.log_user_action(
                OrganisationAction.ACTION_UPDATE_CONTACTS.format(
                    f"{contact.first_name} {contact.last_name}({contact.email})"
                ),
                request,
            )
        except:
            pass

    def generate_pins(self):
        # self.pin_one = self._generate_pin()
        # self.pin_two = self._generate_pin()
        self.admin_pin_one = self._generate_pin()
        self.admin_pin_two = self._generate_pin()
        self.user_pin_one = self._generate_pin()
        self.user_pin_two = self._generate_pin()
        self.save()

    def _generate_pin(self):
        return random_generator()

    def send_organisation_request_link_notification(self, request):
        # Notify each Admin member of request to be linked to org.
        contacts = OrganisationContact.objects.filter(
            organisation_id=self.id, user_role="organisation_admin", user_status="active", is_admin=True
        )
        recipients = [c.email for c in contacts]
        send_organisation_request_link_email_notification(self, request, recipients)

    @property
    def has_no_admins(self):
        return self.contacts.filter(user_role=OrganisationContact.ORG_CONTACT_ROLE_ADMIN).count() < 1

    @staticmethod
    def existence(abn, name=None):
        exists = True
        org = None
        organisation_response = get_search_organisation(name, abn)
        response_status = organisation_response.get("status", None)

        if response_status == status.HTTP_200_OK:
            ledger_org = organisation_response.get("data", {})[0]
            try:
                org = Organisation.objects.get(organisation_id=ledger_org["organisation_id"])
            except Organisation.DoesNotExist:
                exists = False
        else:
            exists = False

        if exists:
            if not org.has_no_admins:
                return {
                    "exists": exists,
                    "id": org.id,
                    "first_five": org.first_five,
                }
            else:
                return {"exists": not org.has_no_admins}
        return {"exists": exists}

    def accept_user(self, user, request):
        with transaction.atomic():
            # try:
            #     UserDelegation.objects.get(organisation=self,user=user)
            #     raise ValidationError('This user has already been linked to {}'.format(str(self.organisation)))
            # except UserDelegation.DoesNotExist:
            delegate = UserDelegation.objects.create(organisation=self, user=user)

            try:
                org_contact = OrganisationContact.objects.get(organisation=self, email=delegate.user.email)
                org_contact.user_status = "active"
                org_contact.save()
            except OrganisationContact.DoesNotExist:
                pass

            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_LINK.format(
                    f"{delegate.user.first_name} {delegate.user.last_name}({delegate.user.email})"
                ),
                request,
            )
            send_organisation_link_email_notification(user, request.user, self, request)

    def decline_user(self, user, request):
        try:
            org_contact = OrganisationContact.objects.get(organisation=self, email=user.email)
            org_contact.user_status = "declined"
            org_contact.save()
        except OrganisationContact.DoesNotExist:
            pass
        OrganisationContactDeclinedDetails.objects.create(officer=request.user, request=org_contact)

        # log linking
        self.log_user_action(
            OrganisationAction.ACTION_CONTACT_DECLINED.format(f"{user.first_name} {user.last_name}({user.email})"),
            request,
        )
        send_organisation_contact_decline_email_notification(user, request.user, self, request)

    def link_user(self, user, request, admin_flag):
        with transaction.atomic():
            try:
                UserDelegation.objects.get(organisation=self, user=user)
                raise ValidationError(f"This user has already been linked to {str(self.organisation)}")
            except UserDelegation.DoesNotExist:
                delegate = UserDelegation.objects.create(organisation=self, user=user)
            if self.first_five_admin:
                is_admin = True
                role = "organisation_admin"
            elif admin_flag:
                role = "organisation_admin"
                is_admin = True
            else:
                role = "organisation_user"
                is_admin = False

            # Create contact person
            try:
                OrganisationContact.objects.create(
                    organisation=self,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    mobile_number=user.mobile_number,
                    phone_number=user.phone_number,
                    fax_number=user.fax_number,
                    email=user.email,
                    user_role=role,
                    user_status="pending",
                    is_admin=is_admin,
                )
            except:
                pass  # user already exists

            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_LINK.format(
                    f"{delegate.user.first_name} {delegate.user.last_name}({delegate.user.email})"
                ),
                request,
            )
            # send email
            send_organisation_link_email_notification(user, request.user, self, request)

    def accept_declined_user(self, user, request):
        with transaction.atomic():
            try:
                UserDelegation.objects.get(organisation=self, user=user)
                raise ValidationError(f"This user has already been linked to {str(self.organisation)}")
            except UserDelegation.DoesNotExist:
                delegate = UserDelegation.objects.create(organisation=self, user=user)
            if self.first_five_admin:
                is_admin = True
                role = "organisation_admin"
            elif admin_flag:
                role = "organisation_admin"
                is_admin = True
            else:
                role = "organisation_user"
                is_admin = False

            try:
                org_contact = OrganisationContact.objects.get(organisation=self, email=delegate.user.email)
                org_contact.user_status = "active"
                org_contact.save()
            except OrganisationContact.DoesNotExist:
                pass

            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_LINK.format(
                    f"{delegate.user.first_name} {delegate.user.last_name}({delegate.user.email})"
                ),
                request,
            )
            # send email
            send_organisation_link_email_notification(user, request.user, self, request)

    def relink_user(self, user, request):
        with transaction.atomic():
            try:
                UserDelegation.objects.get(organisation=self, user=user)
                raise ValidationError(f"This user has not yet been linked to {str(self.organisation)}")
            except UserDelegation.DoesNotExist:
                delegate = UserDelegation.objects.create(organisation=self, user=user)
            try:
                org_contact = OrganisationContact.objects.get(organisation=self, email=delegate.user.email)
                org_contact.user_status = "active"
                org_contact.save()
            except OrganisationContact.DoesNotExist:
                pass
            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_MAKE_CONTACT_REINSTATE.format(
                    f"{delegate.user.first_name} {delegate.user.last_name}({delegate.user.email})"
                ),
                request,
            )
            # send email
            send_organisation_reinstate_email_notification(user, request.user, self, request)

    def unlink_user(self, user, request):
        with transaction.atomic():
            try:
                delegate = UserDelegation.objects.get(organisation=self, user=user)
            except UserDelegation.DoesNotExist:
                raise ValidationError(f"This user is not a member of {str(self.organisation)}")
            # delete contact person
            try:
                org_contact = OrganisationContact.objects.get(organisation=self, email=delegate.user.email)
                if org_contact.user_role == "organisation_admin":
                    if (
                        OrganisationContact.objects.filter(
                            organisation=self, user_role="organisation_admin", user_status="active"
                        ).count()
                        > 1
                    ):
                        org_contact.user_status = "unlinked"
                        org_contact.save()
                        # delete delegate
                        delegate.delete()
                    else:
                        raise ValidationError(
                            "This user can't be unlinked because they are the last Organisation Administrator."
                        )

                else:
                    org_contact.user_status = "unlinked"
                    org_contact.save()
                    # delete delegate
                    delegate.delete()
            except OrganisationContact.DoesNotExist:
                pass

            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_UNLINK.format(
                    f"{delegate.user.first_name} {delegate.user.last_name}({delegate.user.email})"
                ),
                request,
            )
            # send email
            send_organisation_unlink_email_notification(user, request.user, self, request)

    def make_admin_user(self, user, request):
        with transaction.atomic():
            try:
                delegate = UserDelegation.objects.get(organisation=self, user=user)
            except UserDelegation.DoesNotExist:
                raise ValidationError(f"This user is not a member of {str(self.organisation)}")
            # delete contact person
            try:
                org_contact = OrganisationContact.objects.get(organisation=self, email=delegate.user.email)
                org_contact.user_role = "organisation_admin"
                org_contact.is_admin = True
                org_contact.save()
            except OrganisationContact.DoesNotExist:
                pass
            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_MAKE_CONTACT_ADMIN.format(
                    f"{delegate.user.first_name} {delegate.user.last_name}({delegate.user.email})"
                ),
                request,
            )
            # send email
            send_organisation_contact_adminuser_email_notification(user, request.user, self, request)

    def make_user(self, user, request):
        with transaction.atomic():
            try:
                delegate = UserDelegation.objects.get(organisation=self, user=user)
            except UserDelegation.DoesNotExist:
                raise ValidationError(f"This user is not a member of {str(self.organisation)}")
            # delete contact person
            try:
                org_contact = OrganisationContact.objects.get(organisation=self, email=delegate.user.email)
                if org_contact.user_role == "organisation_admin":
                    # Last admin user should not be able to make himself user.
                    if (
                        OrganisationContact.objects.filter(
                            organisation=self, user_role="organisation_admin", user_status="active"
                        ).count()
                        > 1
                    ):
                        org_contact.user_role = "organisation_user"
                        org_contact.is_admin = False
                        org_contact.save()
                    else:
                        raise ValidationError(
                            "This user can't be demoted to a regular user as they are the last Organisation Administrator."
                        )
                else:
                    org_contact.user_role = "organisation_user"
                    org_contact.is_admin = False
                    org_contact.save()

                org_contact.user_role = "organisation_user"
                org_contact.is_admin = False
                org_contact.save()
            except OrganisationContact.DoesNotExist:
                pass
            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_MAKE_CONTACT_USER.format(
                    f"{delegate.user.first_name} {delegate.user.last_name}({delegate.user.email})"
                ),
                request,
            )
            # send email
            send_organisation_contact_user_email_notification(user, request.user, self, request)

    def make_consultant(self, user, request):
        with transaction.atomic():
            try:
                delegate = UserDelegation.objects.get(organisation=self, user=user)
            except UserDelegation.DoesNotExist:
                raise ValidationError(f"This user is not a member of {str(self.organisation)}")
            # delete contact person
            try:
                org_contact = OrganisationContact.objects.get(organisation=self, email=delegate.user.email)

                if org_contact.user_role == "organisation_admin":
                    # Last admin user should not be able to make himself user.
                    if (
                        OrganisationContact.objects.filter(
                            organisation=self, user_role="organisation_admin", user_status="active"
                        ).count()
                        > 1
                    ):
                        org_contact.user_role = "organisation_user"
                        org_contact.is_admin = False
                        org_contact.save()
                    else:
                        raise ValidationError(
                            "This user can't be demoted to a consultant user as they are the last Organisation Administrator."
                        )

                org_contact.user_role = "consultant"
                org_contact.is_admin = False
                org_contact.save()
            except OrganisationContact.DoesNotExist:
                pass
            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_MAKE_CONTACT_CONSULTANT.format(
                    f"{delegate.user.first_name} {delegate.user.last_name}({delegate.user.email})"
                ),
                request,
            )
            # send email
            send_organisation_contact_consultant_email_notification(user, request.user, self, request)

    def suspend_user(self, user, request):
        with transaction.atomic():
            try:
                delegate = UserDelegation.objects.get(organisation=self, user=user)
            except UserDelegation.DoesNotExist:
                raise ValidationError(f"This user is not a member of {str(self.organisation)}")
            # delete contact person
            try:
                org_contact = OrganisationContact.objects.get(organisation=self, email=delegate.user.email)
                org_contact.user_status = "suspended"
                org_contact.save()
            except OrganisationContact.DoesNotExist:
                pass
            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_MAKE_CONTACT_SUSPEND.format(
                    f"{delegate.user.first_name} {delegate.user.last_name}({delegate.user.email})"
                ),
                request,
            )
            # send email
            send_organisation_contact_suspend_email_notification(user, request.user, self, request)

    def reinstate_user(self, user, request):
        with transaction.atomic():
            try:
                delegate = UserDelegation.objects.get(organisation=self, user=user)
            except UserDelegation.DoesNotExist:
                raise ValidationError(f"This user is not a member of {str(self.organisation)}")
            # delete contact person
            try:
                org_contact = OrganisationContact.objects.get(organisation=self, email=delegate.user.email)
                org_contact.user_status = "active"
                org_contact.save()
            except OrganisationContact.DoesNotExist:
                pass
            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_MAKE_CONTACT_REINSTATE.format(
                    f"{delegate.user.first_name} {delegate.user.last_name}({delegate.user.email})"
                ),
                request,
            )
            # send email
            send_organisation_reinstate_email_notification(user, request.user, self, request)

    def can_user_edit(self, email):
        return OrganisationContact.objects.filter(
            organisation=self, is_admin=True, user_status=OrganisationContact.ORG_CONTACT_STATUS_ACTIVE, email=email
        ).exists()

    @property
    def trading_name(self):
        return self.organisation.get("organisation_trading_name", "")

    @property
    def name(self):
        value = self.organisation.get("organisation_name")
        if value is None:
            logger.warning(
                "'organisation_name' key missing from ledger data for organisation_id=%s. Available keys: %s",
                self.organisation_id,
                list(self.organisation.keys()),
            )
        return value or ""

    @property
    def abn(self):
        return self.organisation.get("organisation_abn", "")

    @property
    def address(self):
        return self.organisation.get("postal_address")

    @property
    def address_string(self):
        org_address = self.organisation.get("postal_address")
        if org_address:
            fields = [str(org_address[key]) for key in org_address if org_address[key]]
            return ", ".join(fields)
        else:
            return ""

    # @property
    # def phone_number(self):
    #    return self.organisation["phone_number"]

    @property
    def email(self):
        return self.organisation.get("organisation_email", "")

    @property
    def first_five(self):
        return ",".join([user.get_full_name() for user in self.delegates.all()[:5]])

    @property
    def first_five_admin_names(self):
        qs = OrganisationContact.objects.filter(
            user_role="organisation_admin", is_admin=True, user_status="active", organisation=self
        )
        if qs:
            return ",".join([f"{user.first_name} {user.last_name}" for user in qs[:5]])
        return self.first_five


@python_2_unicode_compatible
class OrganisationContact(SanitiseMixin):
    ORG_CONTACT_STATUS_DRAFT = "draft"
    ORG_CONTACT_STATUS_PENDING = "pending"
    ORG_CONTACT_STATUS_ACTIVE = "active"
    ORG_CONTACT_STATUS_DECLINED = "declined"
    ORG_CONTACT_STATUS_UNLINKED = "unlinked"
    ORG_CONTACT_STATUS_SUSPENDED = "suspended"
    USER_STATUS_CHOICES = (
        (ORG_CONTACT_STATUS_DRAFT, "Draft"),
        (ORG_CONTACT_STATUS_PENDING, "Pending"),
        (ORG_CONTACT_STATUS_ACTIVE, "Active"),
        (ORG_CONTACT_STATUS_DECLINED, "Declined"),
        (ORG_CONTACT_STATUS_UNLINKED, "Unlinked"),
        (ORG_CONTACT_STATUS_SUSPENDED, "Suspended"),
        (
            "contact_form",
            "ContactForm",
        ),  # status 'contact_form' if org contact was added via 'Contact Details' section in manage.vue (allows Org Contact to be distinguished from Org Delegate)
    )
    ORG_CONTACT_ROLE_ADMIN = "organisation_admin"
    ORG_CONTACT_ROLE_USER = "organisation_user"
    ORG_CONTACT_ROLE_CONSULTANT = "consultant"
    USER_ROLE_CHOICES = (
        (ORG_CONTACT_ROLE_ADMIN, "Organisation Admin"),
        (ORG_CONTACT_ROLE_USER, "Organisation User"),
        (ORG_CONTACT_ROLE_CONSULTANT, "Consultant"),
    )
    user_status = models.CharField(
        "Status", max_length=40, choices=USER_STATUS_CHOICES, default=USER_STATUS_CHOICES[0][0]
    )
    user_role = models.CharField("Role", max_length=40, choices=USER_ROLE_CHOICES, default="organisation_user")
    is_admin = models.BooleanField(default=False)
    organisation = models.ForeignKey(Organisation, related_name="contacts", on_delete=models.CASCADE)
    email = models.EmailField(blank=False)
    first_name = models.CharField(max_length=128, blank=False, verbose_name="Given name(s)")
    last_name = models.CharField(max_length=128, blank=False)
    phone_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="phone number", help_text="")
    mobile_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="mobile number", help_text="")
    fax_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="fax number", help_text="")

    class Meta:
        app_label = "disturbance"
        unique_together = (("organisation", "email"),)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    @property
    def can_edit(self):
        """
        :return: True if the application is in one of the editable status.
        """
        return self.is_admin and self.user_status == "active" and self.user_role == "organisation_admin"

    @property
    def check_consultant(self):
        """
        :return: True if the application is in one of the editable status.
        """
        return self.user_status == "active" and self.user_role == "consultant"


class OrganisationContactDeclinedDetails(SanitiseMixin):
    request = models.ForeignKey(OrganisationContact, on_delete=models.CASCADE)
    officer = models.ForeignKey(EmailUser, null=False, on_delete=models.CASCADE)

    class Meta:
        app_label = "commercialoperator"


class UserDelegation(models.Model):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    user = models.ForeignKey(EmailUser, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("organisation", "user"),)
        app_label = "disturbance"


class OrganisationAction(UserAction):
    ACTION_REQUEST_APPROVED = "Organisation Request {} Approved"
    ACTION_LINK = "Linked {}"
    ACTION_UNLINK = "Unlinked {}"
    ACTION_CONTACT_ADDED = "Added new contact {}"
    ACTION_CONTACT_REMOVED = "Removed contact {}"
    ACTION_CONTACT_DECLINED = "Declined contact {}"
    ACTION_MAKE_CONTACT_ADMIN = "Made contact Organisation Admin {}"
    ACTION_MAKE_CONTACT_USER = "Made contact Organisation User {}"
    ACTION_MAKE_CONTACT_CONSULTANT = "Made contact Consultant {}"
    ACTION_ORGANISATIONAL_DETAILS_SAVED_NOT_CHANGED = "Details saved without changes"
    ACTION_ORGANISATIONAL_DETAILS_SAVED_CHANGED = "Details saved with the following changes: \n{}"
    ACTION_ORGANISATIONAL_ADDRESS_DETAILS_SAVED_NOT_CHANGED = "Address Details saved without changes"
    ACTION_ORGANISATIONAL_ADDRESS_DETAILS_SAVED_CHANGED = "Addres Details saved with folowing changes: \n{}"
    ACTION_ORGANISATION_CONTACT_ACCEPT = "Accepted contact {}"
    ACTION_MAKE_CONTACT_SUSPEND = "Suspended contact {}"
    ACTION_MAKE_CONTACT_REINSTATE = "Reinstated contact {}"

    ACTION_UPDATE_ORGANISATION = "Updated organisation name"
    ACTION_UPDATE_ADDRESS = "Updated address"
    ACTION_UPDATE_CONTACTS = "Updated contacts"

    @classmethod
    def log_action(cls, organisation, action, user):
        return cls.objects.create(organisation=organisation, who=user, what=str(action))

    organisation = models.ForeignKey(Organisation, related_name="action_logs", on_delete=models.CASCADE)

    class Meta:
        app_label = "disturbance"


def update_organisation_comms_log_filename(instance, filename):
    return f"organisations/{instance.log_entry.organisation.id}/communications/{instance.id}/{filename}"


class OrganisationLogDocument(LedgerDocument):
    log_entry = models.ForeignKey("OrganisationLogEntry", related_name="documents", on_delete=models.CASCADE)
    _file = models.FileField(max_length=255, upload_to=update_organisation_comms_log_filename, storage=private_storage)

    class Meta:
        app_label = "disturbance"


class OrganisationLogEntry(CommunicationsLogEntry):
    organisation = models.ForeignKey(Organisation, related_name="comms_logs", on_delete=models.CASCADE)

    def save(self, **kwargs):
        # save the request id if the reference not provided
        print(self.__dict__)
        if not self.reference:
            self.reference = self.organisation_id
        super().save(**kwargs)

    class Meta:
        app_label = "disturbance"


class OrganisationRequest(SanitiseFileMixin):
    STATUS_CHOICES = (("with_assessor", "With Assessor"), ("approved", "Approved"), ("declined", "Declined"))
    ORG_REQUEST_ROLE_EMPLOYEE = "employee"
    ORG_REQUEST_ROLE_CONSULTANT = "consultant"
    ROLE_CHOICES = ((ORG_REQUEST_ROLE_EMPLOYEE, "Employee"), (ORG_REQUEST_ROLE_CONSULTANT, "Consultant"))
    TEMPLATE_GROUP_CHOICES = (("apiary", "Apiary"), ("das", "DAS"))
    name = models.CharField(max_length=128, unique=True)
    abn = models.CharField(max_length=50, null=True, blank=True, verbose_name="ABN")
    requester = models.ForeignKey(EmailUser, on_delete=models.CASCADE)
    assigned_officer = models.ForeignKey(
        EmailUser, blank=True, null=True, related_name="org_request_assignee", on_delete=models.CASCADE
    )
    identification = models.FileField(
        max_length=255, upload_to="organisation/requests/", null=True, blank=True, storage=private_storage
    )
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default="with_assessor")
    lodgement_date = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=100, choices=ROLE_CHOICES, default="employee")
    template_group = models.CharField(max_length=100, choices=TEMPLATE_GROUP_CHOICES, default="das")

    class Meta:
        app_label = "disturbance"

    def accept(self, request):
        with transaction.atomic():
            # create_organisation
            create_organisation(self.name, self.abn)
            self.status = "approved"
            self.save()
            self.log_user_action(OrganisationRequestUserAction.ACTION_CONCLUDE_REQUEST.format(self.id), request)
            # Continue with remaining logic
            self.__accept(request)

    def __accept(self, request):
        from disturbance.helpers import is_apiary_org_request_assessor

        if is_apiary_org_request_assessor(request):
            # Check if organisation exists in ledger
            ledger_org = None

            organisation_response = get_search_organisation(self.name, self.abn)
            response_status = organisation_response.get("status", None)

            if response_status == status.HTTP_404_NOT_FOUND:
                raise serializers.ValidationError("Organisation does not exist in the ledger.")

            if response_status != status.HTTP_200_OK:
                raise serializers.ValidationError("Failed to retrieve organisation details from the ledger.")

            ledger_org = organisation_response.get("data", {})[0]

            # Create Organisation in apiary
            org, created = Organisation.objects.get_or_create(organisation_id=ledger_org["organisation_id"])
            # org.generate_pins()
            # Link requester to organisation
            delegate, created = UserDelegation.objects.get_or_create(user=self.requester, organisation=org)

            # log who approved the request
            # org.log_user_action(OrganisationAction.ACTION_REQUEST_APPROVED.format(self.id),request)
            # log who created the link
            org.log_user_action(
                OrganisationAction.ACTION_LINK.format(
                    f"{get_first_name(delegate.user)} {get_last_name(delegate.user)}({delegate.user.email})"
                ),
                request,
            )

            if self.role == OrganisationRequest.ORG_REQUEST_ROLE_CONSULTANT:
                role = OrganisationContact.ORG_CONTACT_ROLE_CONSULTANT
            else:
                role = OrganisationContact.ORG_CONTACT_ROLE_ADMIN

            # Create contact person
            org_contact, _ = OrganisationContact.objects.get_or_create(
                organisation=org,
                email=self.requester.email,
            )

            org_contact.first_name = get_first_name(self.requester)
            org_contact.last_name = get_last_name(self.requester)
            org_contact.mobile_number = self.requester.mobile_number
            org_contact.phone_number = self.requester.phone_number
            org_contact.fax_number = self.requester.fax_number
            org_contact.user_role = role
            org_contact.user_status = OrganisationContact.ORG_CONTACT_STATUS_ACTIVE
            org_contact.is_admin = True
            org_contact.save()

            # send email to requester
            send_organisation_request_accept_email_notification(self, org, request)
            # Notify other Organisation Access Group members of acceptance.
            recipients = list(
                ApiaryOrganisationAccessGroup.objects.last().resolved_members.values_list("email", flat=True)
            )
            if recipients:
                send_org_access_group_request_accept_email_notification(self, request, recipients)
        else:
            raise serializers.ValidationError("User not authorised to approve organisation request")

    def assign_to(self, user, request):
        with transaction.atomic():
            self.assigned_officer = user
            self.save()
            self.log_user_action(OrganisationRequestUserAction.ACTION_ASSIGN_TO.format(user.get_full_name()), request)

    def unassign(self, request):
        with transaction.atomic():
            self.assigned_officer = None
            self.save()
            self.log_user_action(OrganisationRequestUserAction.ACTION_UNASSIGN, request)

    def decline(self, reason, request):
        with transaction.atomic():
            self.status = "declined"
            self.save()
            OrganisationRequestDeclinedDetails.objects.create(officer=request.user, reason=reason, request=self)
            self.log_user_action(OrganisationRequestUserAction.ACTION_DECLINE_REQUEST, request)
            send_organisation_request_decline_email_notification(self, request)

    def send_organisation_request_email_notification(self, request, template_group):
        # user submits a new organisation request
        # send email to organisation access group
        if template_group == "apiary":
            group = ApiaryOrganisationAccessGroup.objects.first()
        else:
            group = OrganisationAccessGroup.objects.first()
        if group and group.filtered_members:
            org_access_recipients = [m.email for m in group.filtered_members]
            send_organisation_request_email_notification(self, request, org_access_recipients)

    def log_user_action(self, action, request):
        return OrganisationRequestUserAction.log_action(self, action, request.user)

    def __str__(self):
        return f"name: {self.name}, id {self.id}"


class ApiaryOrganisationAccessGroupMember(models.Model):
    emailuser = models.ForeignKey(EmailUser, null=False, on_delete=models.CASCADE)

    apiaryorganisationaccessgroup = models.ForeignKey(
        "disturbance.ApiaryOrganisationAccessGroup", null=False, on_delete=models.CASCADE
    )

    class Meta:
        app_label = "disturbance"
        db_table = "disturbance_apiaryorganisationaccessgroup_members"
        unique_together = ("apiaryorganisationaccessgroup", "emailuser")


class ApiaryOrganisationAccessGroup(models.Model):
    site = models.OneToOneField(Site, default="1", on_delete=models.CASCADE)
    members = models.ManyToManyField(
        EmailUser,
        through=ApiaryOrganisationAccessGroupMember,
    )

    def __str__(self):
        return "Apiary Organisation Access Group"

    @property
    def resolved_members(self):
        """
        Manually fetches related EmailUser objects to correctly handle the
        cross-database relationship.

        This property bypasses the ORM's default ManyToMany query, which
        incorrectly queries the 'ledger_db' due to the LedgerDBRouter's
        behavior with the EmailUserRO model.
        """
        # 1. Get member IDs from the intermediate table in the 'default' database.
        member_ids = ApiaryOrganisationAccessGroupMember.objects.filter(apiaryorganisationaccessgroup=self).values_list(
            "emailuser_id", flat=True
        )

        # 2. Use the IDs to fetch EmailUser objects from the 'ledger_db'.
        return EmailUser.objects.using("ledger_db").filter(Q(pk__in=list(member_ids)) | Q(is_superuser=True))

    @property
    def all_members(self):
        return list(self.resolved_members)

    @property
    def filtered_members(self):
        return self.resolved_members

    class Meta:
        app_label = "disturbance"
        verbose_name_plural = "Apiary Organisation access group"


class OrganisationAccessGroupMember(models.Model):
    emailuser = models.ForeignKey(EmailUser, null=False, on_delete=models.CASCADE)

    organisationaccessgroup = models.ForeignKey(
        "disturbance.OrganisationAccessGroup", null=False, on_delete=models.CASCADE
    )

    class Meta:
        app_label = "disturbance"
        db_table = "disturbance_organisationaccessgroup_members"
        unique_together = ("organisationaccessgroup", "emailuser")


# TODO on-cleanup determine if this is needed or can just be replaced with the Apiary Organisation Access Group
class OrganisationAccessGroup(models.Model):
    site = models.OneToOneField(Site, default="1", on_delete=models.CASCADE)
    members = models.ManyToManyField(
        EmailUser,
        through=OrganisationAccessGroupMember,
    )

    @property
    def resolved_members(self):
        """
        Manually fetches related EmailUser objects to correctly handle the cross-database relationship.
        """
        # 1. Get member IDs from the intermediate table in the 'default' database.
        member_ids = OrganisationAccessGroupMember.objects.filter(organisationaccessgroup=self).values_list(
            "emailuser_id", flat=True
        )

        # 2. Use the IDs to fetch EmailUser objects from the 'ledger_db'.
        return EmailUser.objects.using("ledger_db").filter(Q(pk__in=list(member_ids)) | Q(is_superuser=True))

    def __str__(self):
        return "Organisation Access Group"

    @property
    def all_members(self):
        return list(self.resolved_members)

    @property
    def filtered_members(self):
        return self.resolved_members

    class Meta:
        app_label = "disturbance"
        verbose_name_plural = "Organisation access group"


class OrganisationRequestUserAction(UserAction):
    ACTION_LODGE_REQUEST = "Lodge request {}"
    ACTION_ASSIGN_TO = "Assign to {}"
    ACTION_UNASSIGN = "Unassign"
    ACTION_DECLINE_REQUEST = "Decline request"
    # Assessors

    ACTION_CONCLUDE_REQUEST = "Conclude request {}"

    @classmethod
    def log_action(cls, request, action, user):
        return cls.objects.create(request=request, who=user, what=str(action))

    request = models.ForeignKey(OrganisationRequest, related_name="action_logs", on_delete=models.CASCADE)

    class Meta:
        app_label = "disturbance"


class OrganisationRequestDeclinedDetails(SanitiseMixin):
    request = models.ForeignKey(OrganisationRequest, on_delete=models.CASCADE)
    officer = models.ForeignKey(EmailUser, null=False, on_delete=models.CASCADE)
    reason = models.TextField(blank=True)

    class Meta:
        app_label = "disturbance"


def update_organisation_request_comms_log_filename(instance, filename):
    return f"organisation_requests/{instance.log_entry.request.id}/communications/{instance.log_entry.id}/{filename}"


class OrganisationRequestLogDocument(LedgerDocument):
    log_entry = models.ForeignKey("OrganisationRequestLogEntry", related_name="documents", on_delete=models.CASCADE)
    _file = models.FileField(
        max_length=255, upload_to=update_organisation_request_comms_log_filename, storage=private_storage
    )

    class Meta:
        app_label = "disturbance"


class OrganisationRequestLogEntry(CommunicationsLogEntry):
    request = models.ForeignKey(OrganisationRequest, related_name="comms_logs", on_delete=models.CASCADE)

    def save(self, **kwargs):
        # save the request id if the reference not provided
        if not self.reference:
            self.reference = self.request.id
        super().save(**kwargs)

    class Meta:
        app_label = "disturbance"


import reversion

reversion.register(Organisation, follow=["contacts", "action_logs", "comms_logs"])
reversion.register(OrganisationContact)
reversion.register(OrganisationAction)
reversion.register(OrganisationLogEntry)
reversion.register(OrganisationLogDocument)
reversion.register(OrganisationRequest)
reversion.register(UserDelegation)
reversion.register(ApiaryOrganisationAccessGroup)

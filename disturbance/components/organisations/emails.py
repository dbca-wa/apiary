import logging

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.utils.encoding import smart_bytes
from ledger_api_client.ledger_models import EmailUserRO as EmailUser

from disturbance.components.emails.emails import TemplateEmailBase

logger = logging.getLogger(__name__)

SYSTEM_NAME = settings.SYSTEM_NAME_SHORT + " Automated Message"


def get_sender_user():
    sender = settings.DEFAULT_FROM_EMAIL
    try:
        sender_user = EmailUser.objects.get(email__icontains=sender)
    except:
        EmailUser.objects.create(email=sender, password="")
        sender_user = EmailUser.objects.get(email__icontains=sender)
    return sender_user


class OrganisationRequestAcceptNotificationEmail(TemplateEmailBase):
    subject = "Your organisation request has been accepted."
    html_template = "disturbance/emails/organisation_request_accept_notification.html"
    txt_template = "disturbance/emails/organisation_request_accept_notification.txt"


class OrganisationAccessGroupRequestAcceptNotificationEmail(TemplateEmailBase):
    subject = "New organisation request has been submitted."
    html_template = "disturbance/emails/org_access_group_request_accept_notification.html"
    txt_template = "disturbance/emails/org_access_group_request_accept_notification.txt"


class OrganisationRequestNotificationEmail(TemplateEmailBase):
    subject = "An organisation request has been submitted for approval"
    html_template = "disturbance/emails/organisation_request_notification.html"
    txt_template = "disturbance/emails/organisation_request_notification.txt"


class OrganisationRequestDeclineNotificationEmail(TemplateEmailBase):
    subject = "Your organisation request has been declined."
    html_template = "disturbance/emails/organisation_request_decline_notification.html"
    txt_template = "disturbance/emails/organisation_request_decline_notification.txt"


class OrganisationLinkNotificationEmail(TemplateEmailBase):
    subject = "You have been linked to an organisation."
    html_template = "disturbance/emails/organisation_link_notification.html"
    txt_template = "disturbance/emails/organisation_link_notification.txt"


class OrganisationUnlinkNotificationEmail(TemplateEmailBase):
    subject = "You have been unlinked from an organisation."
    html_template = "disturbance/emails/organisation_unlink_notification.html"
    txt_template = "disturbance/emails/organisation_unlink_notification.txt"


class OrganisationContactAdminUserNotificationEmail(TemplateEmailBase):
    subject = "You have been linked as Company Admin Role."
    html_template = "disturbance/emails/organisation_contact_admin_notification.html"
    txt_template = "disturbance/emails/organisation_contact_admin_notification.txt"


class OrganisationContactUserNotificationEmail(TemplateEmailBase):
    subject = "You have been linked as Company User Role."
    html_template = "disturbance/emails/organisation_contact_user_notification.html"
    txt_template = "disturbance/emails/organisation_contact_user_notification.txt"


class OrganisationContactConsultantNotificationEmail(TemplateEmailBase):
    subject = "You have been linked as Company Consultant Role."
    html_template = "disturbance/emails/organisation_contact_consultant_notification.html"
    txt_template = "disturbance/emails/organisation_contact_consultant_notification.txt"


class OrganisationContactSuspendNotificationEmail(TemplateEmailBase):
    subject = "You have been suspended as Company User."
    html_template = "disturbance/emails/organisation_contact_suspend_notification.html"
    txt_template = "disturbance/emails/organisation_contact_suspend_notification.txt"


class OrganisationContactReinstateNotificationEmail(TemplateEmailBase):
    subject = "You have been Reinstated as Company User."
    html_template = "disturbance/emails/organisation_contact_reinstate_notification.html"
    txt_template = "disturbance/emails/organisation_contact_reinstate_notification.txt"


class OrganisationContactDeclineNotificationEmail(TemplateEmailBase):
    subject = "Your organisation link request has been declined."
    html_template = "disturbance/emails/organisation_contact_decline_notification.html"
    txt_template = "disturbance/emails/organisation_contact_decline_notification.txt"


class OrganisationAddressUpdatedNotificationEmail(TemplateEmailBase):
    subject = "An organisations address has been updated"
    html_template = "disturbance/emails/organisation_address_updated_notification.html"
    txt_template = "disturbance/emails/organisation_address_updated_notification.txt"


class OrganisationIdUploadNotificationEmail(TemplateEmailBase):
    subject = "An organisations identification has been uploaded"
    html_template = "disturbance/emails/organisation_id_upload_notification.html"
    txt_template = "disturbance/emails/organisation_id_upload_notification.txt"


class OrganisationRequestLinkNotificationEmail(TemplateEmailBase):
    subject = "An organisation request to be linked has been sent for approval"
    html_template = "disturbance/emails/organisation_request_link_notification.html"
    txt_template = "disturbance/emails/organisation_request_link_notification.txt"


def send_organisation_id_upload_email_notification(emails, organisation, org_contact, request):
    email = OrganisationIdUploadNotificationEmail()

    context = {
        "organisation": organisation,
        "base_email_html": settings.BASE_EMAIL_HTML,
        "base_email_text": settings.BASE_EMAIL_TEXT,
    }

    msg = email.send(emails, context=context)
    sender = get_sender_user()
    _log_org_email(msg, organisation, org_contact, sender=sender)


def send_organisation_request_link_email_notification(org_request, request, contact):
    email = OrganisationRequestLinkNotificationEmail()

    url = request.build_absolute_uri(f"/external/organisations/manage/{org_request.id}")

    context = {
        "request": org_request,
        "url": url,
        "base_email_html": settings.BASE_EMAIL_HTML,
        "base_email_text": settings.BASE_EMAIL_TEXT,
    }

    msg = email.send(contact, context=context)
    sender = get_sender_user()
    _log_org_email(msg, org_request, request.user, sender=sender)


def send_organisation_reinstate_email_notification(linked_user, linked_by, organisation, request):
    email = OrganisationContactReinstateNotificationEmail()

    context = {
        "user": linked_user,
        "linked_by": linked_by,
        "organisation": organisation,
        "base_email_html": settings.BASE_EMAIL_HTML,
        "base_email_text": settings.BASE_EMAIL_TEXT,
    }
    all_ccs = []
    if organisation.email:
        cc_list = organisation.email
        if cc_list:
            all_ccs = [cc_list]

    msg = email.send(linked_user.email, cc=all_ccs, context=context)
    sender = get_sender_user()
    _log_org_email(msg, organisation, linked_user, sender=sender)


def send_organisation_contact_suspend_email_notification(linked_user, linked_by, organisation, request):
    email = OrganisationContactSuspendNotificationEmail()

    context = {
        "user": linked_user,
        "linked_by": linked_by,
        "organisation": organisation,
        "base_email_html": settings.BASE_EMAIL_HTML,
        "base_email_text": settings.BASE_EMAIL_TEXT,
    }
    all_ccs = []
    if organisation.email:
        cc_list = organisation.email
        if cc_list:
            all_ccs = [cc_list]

    msg = email.send(linked_user.email, cc=all_ccs, context=context)
    sender = get_sender_user()
    _log_org_email(msg, organisation, linked_user, sender=sender)


def send_organisation_contact_decline_email_notification(user_contact, deleted_by, organisation, request):
    email = OrganisationContactDeclineNotificationEmail()

    context = {
        "user": user_contact,
        "linked_by": deleted_by,
        "organisation": organisation,
        "base_email_html": settings.BASE_EMAIL_HTML,
        "base_email_text": settings.BASE_EMAIL_TEXT,
    }
    all_ccs = []
    if organisation.email:
        cc_list = organisation.email
        if cc_list:
            all_ccs = [cc_list]

    msg = email.send(user_contact.email, cc=all_ccs, context=context)
    sender = get_sender_user()
    _log_org_email(msg, organisation, user_contact, sender=sender)


def send_organisation_contact_user_email_notification(linked_user, linked_by, organisation, request):
    email = OrganisationContactUserNotificationEmail()

    context = {
        "user": linked_user,
        "linked_by": linked_by,
        "organisation": organisation,
        "base_email_html": settings.BASE_EMAIL_HTML,
        "base_email_text": settings.BASE_EMAIL_TEXT,
    }
    all_ccs = []
    if organisation.email:
        cc_list = organisation.email
        if cc_list:
            all_ccs = [cc_list]

    msg = email.send(linked_user.email, cc=all_ccs, context=context)
    sender = get_sender_user()
    _log_org_email(msg, organisation, linked_user, sender=sender)


def send_organisation_contact_consultant_email_notification(linked_user, linked_by, organisation, request):
    email = OrganisationContactConsultantNotificationEmail()

    context = {
        "user": linked_user,
        "linked_by": linked_by,
        "organisation": organisation,
        "base_email_html": settings.BASE_EMAIL_HTML,
        "base_email_text": settings.BASE_EMAIL_TEXT,
    }
    all_ccs = []
    if organisation.email:
        cc_list = organisation.email
        if cc_list:
            all_ccs = [cc_list]

    msg = email.send(linked_user.email, cc=all_ccs, context=context)
    sender = get_sender_user()
    _log_org_email(msg, organisation, linked_user, sender=sender)


def send_organisation_contact_adminuser_email_notification(linked_user, linked_by, organisation, request):
    email = OrganisationContactAdminUserNotificationEmail()

    context = {
        "user": linked_user,
        "linked_by": linked_by,
        "organisation": organisation,
        "base_email_html": settings.BASE_EMAIL_HTML,
        "base_email_text": settings.BASE_EMAIL_TEXT,
    }

    all_ccs = []
    if organisation.email:
        cc_list = organisation.email
        if cc_list:
            all_ccs = [cc_list]
    msg = email.send(linked_user.email, cc=all_ccs, context=context)
    sender = get_sender_user()
    _log_org_email(msg, organisation, linked_user, sender=sender)


def send_organisation_link_email_notification(linked_user, linked_by, organisation, request):
    email = OrganisationLinkNotificationEmail()

    context = {
        "user": linked_user,
        "linked_by": linked_by,
        "organisation": organisation,
        "base_email_html": settings.BASE_EMAIL_HTML,
        "base_email_text": settings.BASE_EMAIL_TEXT,
    }

    all_ccs = []
    if organisation.email:
        cc_list = organisation.email
        if cc_list:
            all_ccs = [cc_list]

    msg = email.send(linked_user.email, cc=all_ccs, context=context)
    sender = get_sender_user()
    _log_org_email(msg, organisation, linked_user, sender=sender)


def send_organisation_request_email_notification(org_request, request, contact):
    email = OrganisationRequestNotificationEmail()

    url = request.build_absolute_uri(f"/internal/organisations/access/{org_request.id}")
    if "-internal" not in url:
        site_prefix = request.META["HTTP_HOST"].split(".")[0]
        url = "{0}://{1}{2}.{3}{4}".format(
            request.scheme, site_prefix, "-internal", settings.SITE_DOMAIN, url.split(request.get_host())[1]
        )

    context = {
        "request": request.data,
        "url": url,
        "base_email_html": settings.BASE_EMAIL_HTML,
        "base_email_text": settings.BASE_EMAIL_TEXT,
    }

    msg = email.send(contact, context=context)
    sender = get_sender_user()
    _log_org_request_email(msg, org_request, sender=sender)


def send_organisation_unlink_email_notification(unlinked_user, unlinked_by, organisation, request):
    email = OrganisationUnlinkNotificationEmail()

    context = {
        "user": unlinked_user,
        "unlinked_by": unlinked_by,
        "organisation": organisation,
        "base_email_html": settings.BASE_EMAIL_HTML,
        "base_email_text": settings.BASE_EMAIL_TEXT,
    }
    all_ccs = []
    if organisation.email:
        cc_list = organisation.email
        if cc_list:
            all_ccs = [cc_list]

    msg = email.send(unlinked_user.email, cc=all_ccs, context=context)
    sender = get_sender_user()
    _log_org_email(msg, organisation, unlinked_user, sender=sender)


def send_organisation_request_accept_email_notification(org_request, organisation, request):
    email = OrganisationRequestAcceptNotificationEmail()

    context = {
        "request": org_request,
        "base_email_html": settings.BASE_EMAIL_HTML,
        "base_email_text": settings.BASE_EMAIL_TEXT,
    }

    msg = email.send(org_request.requester.email, context=context)
    sender = get_sender_user()
    _log_org_request_email(msg, org_request, sender=sender)
    _log_org_email(msg, organisation, org_request.requester, sender=sender)


def send_org_access_group_request_accept_email_notification(org_request, request, recipient_list):
    email = OrganisationAccessGroupRequestAcceptNotificationEmail()

    url = request.build_absolute_uri(f"/internal/organisations/access/{org_request.id}")
    if "-internal" not in url:
        url = f"-internal.{settings.SITE_DOMAIN}".join(url.split("." + settings.SITE_DOMAIN))

    context = {
        "name": request.data.get("name"),
        "abn": request.data.get("abn"),
        "url": url,
        "base_email_html": settings.BASE_EMAIL_HTML,
        "base_email_text": settings.BASE_EMAIL_TEXT,
    }

    msg = email.send(recipient_list, context=context)
    sender = get_sender_user()
    _log_org_request_email(msg, org_request, sender=sender)


def send_organisation_request_decline_email_notification(org_request, request):
    email = OrganisationRequestDeclineNotificationEmail()

    context = {
        "request": org_request,
        "base_email_html": settings.BASE_EMAIL_HTML,
        "base_email_text": settings.BASE_EMAIL_TEXT,
    }

    msg = email.send(org_request.requester.email, context=context)
    sender = get_sender_user()
    _log_org_request_email(msg, org_request, sender=sender)


def send_organisation_address_updated_email_notification(
    address_updated_by, ledger_organisation, wc_organisation, request
):
    from disturbance.components.organisations.models import OrganisationContact

    email = OrganisationAddressUpdatedNotificationEmail()

    context = {
        "address_updated_by": address_updated_by,
        "organisation": ledger_organisation,
        "base_email_html": settings.BASE_EMAIL_HTML,
        "base_email_text": settings.BASE_EMAIL_TEXT,
    }

    for org_contact in OrganisationContact.objects.filter(user_role="organisation_admin", organisation=wc_organisation):
        msg = email.send(org_contact.email, context=context)
        sender = get_sender_user()


def _log_org_request_email(email_message, request, sender=None):
    from disturbance.components.organisations.models import OrganisationRequestLogEntry

    if isinstance(
        email_message,
        (
            EmailMultiAlternatives,
            EmailMessage,
        ),
    ):
        text = email_message.body
        subject = email_message.subject
        fromm = smart_bytes(sender) if sender else smart_bytes(email_message.from_email)
        # the to email is normally a list
        if isinstance(email_message.to, list):
            to = ",".join(email_message.to)
        else:
            to = smart_bytes(email_message.to)
        # we log the cc and bcc in the same cc field of the log entry as a ',' comma separated string
        all_ccs = []
        if email_message.cc:
            all_ccs += list(email_message.cc)
        if email_message.bcc:
            all_ccs += list(email_message.bcc)
        all_ccs = ",".join(all_ccs)

    else:
        text = smart_bytes(email_message)
        subject = ""
        to = request.requester.email
        fromm = smart_bytes(sender) if sender else SYSTEM_NAME
        all_ccs = ""

    customer = request.requester

    staff = sender

    kwargs = {
        "subject": subject,
        "text": text,
        "request": request,
        "customer": customer,
        "staff": staff,
        "to": to,
        "fromm": fromm,
        "cc": all_ccs,
    }

    email_entry = OrganisationRequestLogEntry.objects.create(**kwargs)

    return email_entry


def _log_org_email(email_message, organisation, customer, sender=None):
    from disturbance.components.organisations.models import OrganisationLogEntry

    if isinstance(
        email_message,
        (
            EmailMultiAlternatives,
            EmailMessage,
        ),
    ):
        text = email_message.body
        subject = email_message.subject
        fromm = smart_bytes(sender) if sender else smart_bytes(email_message.from_email)
        # the to email is normally a list
        if isinstance(email_message.to, list):
            to = ",".join(email_message.to)
        else:
            to = smart_bytes(email_message.to)
        # we log the cc and bcc in the same cc field of the log entry as a ',' comma separated string
        all_ccs = []
        if email_message.cc:
            all_ccs += list(email_message.cc)
        if email_message.bcc:
            all_ccs += list(email_message.bcc)
        all_ccs = ",".join(all_ccs)

    else:
        text = smart_bytes(email_message)
        subject = ""
        to = customer
        fromm = smart_bytes(sender) if sender else SYSTEM_NAME
        all_ccs = ""

    customer = customer
    staff = sender

    kwargs = {
        "subject": subject,
        "text": text,
        "organisation": organisation,
        "customer": customer,
        "staff": staff,
        "to": to,
        "fromm": fromm,
        "cc": all_ccs,
    }

    email_entry = OrganisationLogEntry.objects.create(**kwargs)

    return email_entry

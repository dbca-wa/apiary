import logging
from urllib.parse import urlparse, urlunparse

# These functionare here to avoid circular import


def _normalize_url_parts(value):
    """Extract (scheme, netloc) whether given as 'host.com', 'https://host.com',

    'localhost:8000', or 'http://localhost:8000'.
    Ignores placeholder strings like 'APIARY_INTERNAL_URL not configured'.
    """
    if not value:
        return None, None

    val_str = str(value).strip()

    # Treat empty, "none", "not configured", or strings with spaces as unconfigured
    if val_str.lower() in ("none", "") or "not configured" in val_str.lower() or " " in val_str:
        return None, None

    parsed = urlparse(val_str if "://" in val_str else f"//{val_str}")
    netloc = parsed.netloc.lower()
    scheme = parsed.scheme.lower() if parsed.scheme else None

    if not scheme:
        # Default to http for local dev / cluster local domains, otherwise https
        scheme = "http" if ("localhost" in netloc or "127.0.0.1" in netloc or ".local" in netloc) else "https"

    return scheme, netloc


def _prepare_url(url, ext_host, int_host):
    """Disambiguate schemeless host URLs from true relative paths:

    - 'apiary-dev.../path' -> '//apiary-dev.../path' (recognized as netloc)
    - '/internal/path'     -> '/internal/path'        (recognized as path)
    - 'internal/path'      -> '/internal/path'        (recognized as path)
    """
    if not url:
        return ""

    url = url.strip()

    # 1. Already has scheme or protocol-relative slashes
    if "://" in url or url.startswith("//"):
        return url

    # 2. True relative path with leading slash
    if url.startswith("/"):
        return url

    # 3. Schemeless domain URL (e.g. 'apiary-dev.dbca.wa.gov.au/path')
    lower_url = url.lower()
    if (ext_host and lower_url.startswith(ext_host)) or (int_host and lower_url.startswith(int_host)):
        return f"//{url}"

    # 4. Relative path missing a leading slash (e.g. 'internal/proposal/1234')
    return f"/{url}"


def convert_external_url_to_internal_url(url):
    from django.conf import settings  # Prevents circular imports

    ext_scheme, ext_host = _normalize_url_parts(getattr(settings, "APIARY_EXTERNAL_URL", None))
    int_scheme, int_host = _normalize_url_parts(getattr(settings, "APIARY_INTERNAL_URL", None))

    target_host = int_host or ext_host
    target_scheme = int_scheme or ext_scheme or "https"

    if not target_host or not url:
        return url

    # Fix schemeless domains before urlparse sees them
    cleaned_url = _prepare_url(url, ext_host, int_host)
    parsed = urlparse(cleaned_url)

    # 1. True relative path (e.g. '/internal/proposal/1234')
    if not parsed.netloc:
        path = parsed.path if parsed.path.startswith("/") else f"/{parsed.path}"
        return urlunparse(
            (
                target_scheme,
                target_host,
                path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )

    # 2. Already internal -> ensure it has a scheme and return
    if int_host and (parsed.netloc.lower() == int_host or (parsed.hostname and parsed.hostname.lower() == int_host)):
        return urlunparse(parsed._replace(scheme=target_scheme)) if not parsed.scheme else url

    # 3. Match external netloc -> swap to internal
    if ext_host and parsed.netloc.lower() == ext_host:
        return urlunparse(parsed._replace(scheme=target_scheme, netloc=target_host))

    # 4. Match external hostname with custom port
    if ext_host and parsed.hostname and parsed.hostname.lower() == ext_host:
        port_suffix = f":{parsed.port}" if parsed.port and ":" not in target_host else ""
        return urlunparse(parsed._replace(scheme=target_scheme, netloc=f"{target_host}{port_suffix}"))

    return url


def convert_internal_url_to_external_url(url):
    from django.conf import settings  # Prevents circular imports

    ext_scheme, ext_host = _normalize_url_parts(getattr(settings, "APIARY_EXTERNAL_URL", None))
    int_scheme, int_host = _normalize_url_parts(getattr(settings, "APIARY_INTERNAL_URL", None))

    target_host = ext_host or int_host
    target_scheme = ext_scheme or int_scheme or "https"

    if not target_host or not url:
        return url

    # Fix schemeless domains before urlparse sees them
    cleaned_url = _prepare_url(url, ext_host, int_host)
    parsed = urlparse(cleaned_url)

    # 1. True relative path (e.g. '/external/proposal/1234')
    if not parsed.netloc:
        path = parsed.path if parsed.path.startswith("/") else f"/{parsed.path}"
        return urlunparse(
            (
                target_scheme,
                target_host,
                path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )

    # 2. Already external -> ensure it has a scheme and return
    if ext_host and (parsed.netloc.lower() == ext_host or (parsed.hostname and parsed.hostname.lower() == ext_host)):
        return urlunparse(parsed._replace(scheme=target_scheme)) if not parsed.scheme else url

    # 3. Match internal netloc -> swap to external
    if int_host and parsed.netloc.lower() == int_host:
        return urlunparse(parsed._replace(scheme=target_scheme, netloc=target_host))

    # 4. Match internal hostname with custom port
    if int_host and parsed.hostname and parsed.hostname.lower() == int_host:
        port_suffix = f":{parsed.port}" if parsed.port and ":" not in target_host else ""
        return urlunparse(parsed._replace(scheme=target_scheme, netloc=f"{target_host}{port_suffix}"))

    return url


from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import cache
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from ledger_api_client.ledger_models import UsersInGroup
from ledger_api_client.utils import get_organisation
from rest_framework import serializers

from disturbance.components.main.models import MapLayer
from disturbance.components.organisations.models import ApiaryOrganisationAccessGroupMember
from disturbance.components.proposals.models import (
    ApiaryApproverGroupMember,
    ApiaryAssessorGroupMember,
    ApiaryReferralGroupMember,
)

from .request_cache import per_request_cache

logger = logging.getLogger(__name__)


def belongs_to(user, group_name):
    """
    Check if the user belongs to the given group.
    :param user:
    :param group_name:
    :return:
    """
    group = Group.objects.filter(name=group_name)
    if group.exists():
        return user.id in list(
            UsersInGroup.objects.filter(group_id=group.first().id).values_list("emailuser_id", flat=True)
        )
    else:
        return False


# NOTE: this is an env settings based group
def is_apiary_admin(request):
    return request.user.is_authenticated and (belongs_to(request.user, settings.APIARY_ADMIN_GROUP))


def is_in_organisation_contacts(request, organisation):
    return request.user.email in organisation.contacts.all().values_list("email", flat=True)


# NOTE: this is an env settings based group - consider renaming or replacing to avoid confusion
def is_approved_external_user(request):
    if belongs_to(request.user, settings.APPROVED_APIARY_EXTERNAL_USERS_GROUP):
        return True
    return False


def is_apiary_approver(request):
    return (
        request
        and request.user
        and (
            ApiaryApproverGroupMember.objects.filter(emailuser_id=request.user.id).exists() or request.user.is_superuser
        )
    )


def is_apiary_assessor(request):
    return (
        request
        and request.user
        and (
            ApiaryAssessorGroupMember.objects.filter(emailuser_id=request.user.id).exists() or request.user.is_superuser
        )
    )


def is_apiary_referrer(request):
    return (
        request
        and request.user
        and (
            ApiaryReferralGroupMember.objects.filter(emailuser_id=request.user.id).exists() or request.user.is_superuser
        )
    )


def is_apiary_org_request_assessor(request):
    return (
        request
        and request.user
        and (
            ApiaryOrganisationAccessGroupMember.objects.filter(emailuser_id=request.user.id).exists()
            or request.user.is_superuser
        )
    )


def is_internal(request):
    return (
        request
        and request.user
        and (
            request.user.is_superuser
            or is_apiary_admin(request)
            or is_approved_external_user(request)
            or is_apiary_approver(request)
            or is_apiary_assessor(request)
            or is_apiary_referrer(request)
            or is_apiary_org_request_assessor(request)
        )
    )


def get_all_officers():
    return EmailUser.objects.filter(groups__name="Disturbance Admin")


def is_authorised_to_modify(request, instance):
    authorised = True

    # print('1. Application', instance.application_type )
    # print("2. Apiary", str(instance.application_type) == "Apiary")

    # Getting Organisation is different in DAS and Apiary
    if str(instance.application_type) == "Apiary":
        # Get Organisation if in Apiary
        applicant = instance.relevant_applicant
        # print("3. Apiary Applicant", applicant)
    else:
        # Get Organisation if in DAS
        # There can only ever be one Organisation associated with an application so it is
        # ok to just pull the first element from organisation_set.
        applicant = instance.applicant.organisation.organisation_set.all()[0]
        # print("4. DAS Applicant", applicant)
    applicantIsIndividual = isinstance(applicant, EmailUser)
    # print('5. applicantIsIndividual', applicantIsIndividual)
    if is_internal(request):
        # the status must be 'with_assessor'
        authorised &= instance.processing_status == "with_assessor"
        # print("6. Internal with assessor", instance.processing_status == 'with_assessor')
        # the user must be an assessor for this type of application
        authorised &= instance.can_process()
        # print('7. Can process', instance.can_process())
    else:
        # the status of the application must be DRAFT for customer to modify
        authorised &= instance.processing_status == "draft"
        # print('8. Processing status draft', instance.processing_status == 'draft')
        if applicantIsIndividual:
            # it is an individual so the applicant and submitter must be the same
            authorised &= str(request.user.email) == str(instance.relevant_applicant)
            # print('9. Indiv submitter matches applicant', str(request.user.email) == str(instance.relevant_applicant))
        else:
            # the applicant is an organisation so make sure the submitter is in the organisation
            authorised &= is_in_organisation_contacts(request, instance.relevant_applicant)
            # print('10. Applicant is in Org', is_in_organisation_contacts(request, instance.relevant_applicant))

    # print('11. Authorised', authorised)
    if not authorised:
        raise serializers.ValidationError("You are not authorised to modify this application.")


def is_authorised_to_modify_draft(request, instance):
    authorised = True
    applicant = instance.relevant_applicant

    applicantIsIndividual = isinstance(applicant, EmailUser)
    if instance.processing_status == "draft":
        if request.user and request.user.is_authenticated:
            # the status of the application must be DRAFT for customer to modify
            # NOTE: internal users that are apiary assessors can also edit if in draft
            if is_internal(request):
                authorised &= is_apiary_assessor(request) or request.user.is_superuser
            elif applicantIsIndividual:
                # it is an individual so the applicant and submitter must be the same
                authorised &= str(request.user.email) == str(instance.relevant_applicant)
            else:
                # the applicant is an organisation so make sure the submitter is in the organisation
                authorised &= is_in_organisation_contacts(request, instance.relevant_applicant)
        else:
            authorised = False
    else:
        if is_internal(request):
            # the status must be 'with_assessor'
            # the user must be an assessor for this type of application
            authorised &= instance.can_assess()
        else:
            authorised = False

    if not authorised:
        raise serializers.ValidationError("You are not authorised to modify this application.")


def get_proxy_cache():
    proxy_cache_dumped_data = cache.get("utils_cache.get_proxy_cache()")
    proxy_cache_array = []
    if proxy_cache_dumped_data is None:
        proxy_cache_query = MapLayer.objects.all()

        for pr in proxy_cache_query:
            proxy_cache_array.append({"layer_name": pr.layer_name, "cache_expiry": pr.cache_expiry})

        cache.set("utils_cache.get_proxy_cache()", proxy_cache_array, 86400)
    else:
        proxy_cache_array = proxy_cache_dumped_data
    return proxy_cache_array


@per_request_cache
def is_internal_user(user):
    return (
        user
        and hasattr(user, "id")
        and (
            user.is_superuser
            or belongs_to(user, settings.APIARY_ADMIN_GROUP)
            or belongs_to(user, settings.APPROVED_APIARY_EXTERNAL_USERS_GROUP)
            or ApiaryApproverGroupMember.objects.filter(emailuser_id=user.id).exists()
            or ApiaryAssessorGroupMember.objects.filter(emailuser_id=user.id).exists()
            or ApiaryReferralGroupMember.objects.filter(emailuser_id=user.id).exists()
            or ApiaryOrganisationAccessGroupMember.objects.filter(emailuser_id=user.id).exists()
        )
    )


@per_request_cache
def get_cached_ledger_organisation(organisation_id):
    """
    This is safe because it's keyed by an integer.
    Multiple model instances calling this with ID 50
    will only trigger one network call.
    """
    return get_organisation(organisation_id).get("data")

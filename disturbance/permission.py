import logging

from disturbance.components.organisations.models import Organisation
from disturbance.helpers import is_internal

logger = logging.getLogger(__name__)


def organisation_permissions(request, org_id):
    try:
        organisation = Organisation.objects.get(organisation_id=org_id)
    except Organisation.DoesNotExist:
        # We don't give away information to the caller, we simply log a warning and return False
        logger.warning(f"No Organisation exists with organisation_id={org_id}")
        return False

    user = request.user

    # Internal users can access any organisation, external users must be an organisation administrator
    return is_internal(user) or (user.is_authenticated and organisation.can_user_edit(user.email))

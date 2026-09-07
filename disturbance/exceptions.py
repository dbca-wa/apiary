import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class ReferralNotAuthorized(PermissionDenied):
    default_detail = "You are not authorised to work on this referral"
    default_code = "referral_not_authorized"


class ProposalNotAuthorized(PermissionDenied):
    default_detail = "You are not authorised to work on this proposal"
    default_code = "proposal_not_authorized"


class ReferralCanNotSend(PermissionDenied):
    default_detail = "You can only send referrals sent from an assessor"
    default_code = "referral_level_send_unauthorized"


class ProposalReferralCannotBeSent(PermissionDenied):
    default_detail = "Referrals can only be sent if it is in the right processing status"
    default_code = "proposal_referral_cannot_be_sent"


class ProposalNotComplete(APIException):
    status_code = 400
    default_detail = "The proposal is not complete"
    default_code = "proposal_incoplete"


class ProposalMissingFields(APIException):
    status_code = 400
    default_detail = "The proposal has missing required fields"
    default_code = "proposal_missing_fields"


class InternalServerError(APIException):
    status_code = 500
    default_detail = "A server error occurred."
    default_code = "internal_server_error"


def custom_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            exc = DRFValidationError(detail=exc.message_dict)
        elif hasattr(exc, "messages"):
            exc = DRFValidationError(detail=exc.messages)
        else:
            exc = DRFValidationError(detail=[str(exc.message)])

    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(response.data, list):
            response.data = {"non_field_errors": [str(item) for item in response.data]}

        elif isinstance(response.data, dict) and "detail" in response.data and "non_field_errors" not in response.data:
            response.data["non_field_errors"] = [str(response.data["detail"])]

        return response

    logger.exception(f"Server Error: {exc}", exc_info=exc)
    return Response(
        {"non_field_errors": ["An unexpected server error occurred."]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

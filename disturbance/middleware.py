import hashlib
import logging
import re
from urllib.parse import quote_plus

from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from reversion.middleware import RevisionMiddleware
from reversion.views import _request_creates_revision

from disturbance.components.proposals.models import Proposal
from disturbance.helpers import is_internal

from .request_cache import _request_cache

logger = logging.getLogger(__name__)

CHECKOUT_PATH = re.compile("^/ledger/checkout/checkout")


class FirstTimeNagScreenMiddleware:
    """
    Generic FirstTimeNagScreenMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def process_view(self, request, view_func, view_args, view_kwargs):
        return None

    def __call__(self, request):

        if "static" in request.path:
            return self.get_response(request)

        first_time_nag = FirstTimeDefaultNag()
        response = first_time_nag.process_request(request)
        if not response:
            return self.get_response(request)
        else:
            return response


class FirstTimeDefaultNag:
    """
    A specialised FirstTimeNagScreenMiddleware for non WildlifeLicensing.
    """

    def process_request(self, request):

        if "static" in request.path:
            return None

        if (
            request.method == "GET"
            and request.user.is_authenticated
            and "api" not in request.path
            and "admin" not in request.path
            and "ledger-private" not in request.path
            and "static" not in request.path
            and "/ledger-ui/" not in request.get_full_path()
            and "/firsttime/" not in request.get_full_path()
        ):
            path_first_time = "/ledger-ui/accounts-firsttime"
            if (
                (not request.user.first_name)
                or (not request.user.last_name)
                or (not request.user.residential_address)
                or (not (request.user.phone_number or request.user.mobile_number))
            ):
                path_logout = reverse("logout")
                if request.path not in (path_first_time, path_logout):
                    return redirect(path_first_time + "?next=" + quote_plus(request.get_full_path()))

        return None


class RevisionOverrideMiddleware(RevisionMiddleware):
    """
    Wraps the entire request in a revision.

    override venv/lib/python2.7/site-packages/reversion/middleware.py
    """

    # exclude ledger payments/checkout from revision - hack to overcome basket (lagging status) issue/conflict with reversion
    def request_creates_revision(self, request):
        return _request_creates_revision(request) and "checkout" not in request.get_full_path()


class CacheControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path[:5] == "/api/" or request.path == "/":
            response["Cache-Control"] = "private, no-store"
        elif request.path[:8] == "/static/":
            response["Cache-Control"] = "public, max-age=86400"
        else:
            response["Cache-Control"] = "private, no-store"
        return response


class PaymentSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def process_view(self, request, view_func, view_args, view_kwargs):

        redirect_path = "internal" if is_internal(request) else "external"

        if request.user.is_authenticated and (
            CHECKOUT_PATH.match(request.path)
            or request.path.startswith("/ledger-api/process-payment")
            or request.path.startswith("/ledger-api/payment-details")
        ):
            if "payment_pk" in request.session:
                if request.path.startswith("/ledger-api/process-payment"):
                    checkouthash = hashlib.sha256(str(request.session["payment_pk"]).encode("utf-8")).hexdigest()
                    checkouthash_cookie = request.COOKIES.get("checkouthash")
                    validation_cookie = request.COOKIES.get(request.POST.get("payment-csrfmiddlewaretoken"))

                    proposal_count = Proposal.objects.filter(pk=request.session["payment_pk"]).count()

                    if (
                        checkouthash_cookie != checkouthash
                        or checkouthash_cookie != validation_cookie
                        or proposal_count == 0
                    ):
                        url_redirect = reverse(redirect_path)
                        response = HttpResponse(
                            "<script> window.location='"
                            + url_redirect
                            + "';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"
                            + url_redirect
                            + "'> Redirecting please wait: "
                            + url_redirect
                            + "</a><div></div></center>"
                        )
                        return response
            else:
                if request.path.startswith("/ledger-api/process-payment"):
                    url_redirect = reverse(redirect_path)
                    response = HttpResponse(
                        "<script> window.location='"
                        + url_redirect
                        + "';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"
                        + url_redirect
                        + "'> Redirecting please wait: "
                        + url_redirect
                        + "</a><div></div></center>"
                    )
                    return response

        return None

    def __call__(self, request):

        response = self.get_response(request)
        redirect_path = "internal" if is_internal(request) else "external"

        if request.user.is_authenticated and (
            CHECKOUT_PATH.match(request.path)
            or request.path.startswith("/ledger-api/process-payment")
            or request.path.startswith("/ledger-api/payment-details")
        ):
            if "payment_pk" in request.session:
                try:
                    proposal_count = Proposal.objects.get(pk=request.session["payment_pk"])
                except Exception:
                    del request.session["payment_pk"]
                    return response

                if request.path.startswith("/ledger-api/process-payment"):
                    if "payment_pk" not in request.session:
                        url_redirect = reverse(redirect_path)
                        response = HttpResponse(
                            "<script> window.location='"
                            + url_redirect
                            + "';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"
                            + url_redirect
                            + "'> Redirecting please wait: "
                            + url_redirect
                            + "</a><div></div></center>"
                        )
                        return response

                    checkouthash = hashlib.sha256(str(request.session["payment_pk"]).encode("utf-8")).hexdigest()
                    checkouthash_cookie = request.COOKIES.get("checkouthash")
                    validation_cookie = request.COOKIES.get(request.POST.get("payment-csrfmiddlewaretoken"))

                    proposal_count = Proposal.objects.filter(pk=request.session["payment_pk"]).count()

                    if (
                        checkouthash_cookie != checkouthash
                        or checkouthash_cookie != validation_cookie
                        or proposal_count == 0
                    ):
                        url_redirect = reverse(redirect_path)
                        response = HttpResponse(
                            "<script> window.location='"
                            + url_redirect
                            + "';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"
                            + url_redirect
                            + "'> Redirecting please wait: "
                            + url_redirect
                            + "</a><div></div></center>"
                        )
                        return response
            else:
                if request.path.startswith("/ledger-api/process-payment"):
                    url_redirect = reverse(redirect_path)
                    response = HttpResponse(
                        "<script> window.location='"
                        + url_redirect
                        + "';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"
                        + url_redirect
                        + "'> Redirecting please wait: "
                        + url_redirect
                        + "</a><div></div></center>"
                    )
                    return response

            # force a redirect if in the checkout
            if ("payment_pk" not in request.session) and CHECKOUT_PATH.match(request.path):
                url_redirect = reverse(redirect_path)
                response = HttpResponse(
                    "<script> window.location='"
                    + url_redirect
                    + "';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"
                    + url_redirect
                    + "'> Redirecting please wait: "
                    + url_redirect
                    + "</a><div></div></center>"
                )
                return response

        return response


class PerRequestCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _request_cache.set({})  # Start cache
        try:
            return self.get_response(request)
        finally:
            _request_cache.reset(token)  # Destroy cache

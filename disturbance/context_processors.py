from confy import env
from django.conf import settings
from disturbance.components.main.utils import get_template_group
from disturbance.settings import (
    TEMPLATE_HEADER_LOGO,
    TEMPLATE_TITLE,
)
from ledger_api_client.helpers import is_payment_admin
from disturbance.settings import KB_SERVER_URL, KB_BASEMAP_STREET_LAYER, KB_BASEMAP_SATELLITE_LAYER
import logging
from ledger_api_client import utils as ledger_api_utils
import hashlib

logger = logging.getLogger(__name__)

def apiary_url(request):
    PUBLIC_URL = 'https://apiary.dbca.wa.gov.au/'

    is_payment_officer = is_payment_admin(request.user)
    lt = ledger_api_utils.get_ledger_totals()

    checkouthash = None
    if 'payment_pk' in request.session:
        checkouthash =  hashlib.sha256(str(request.session["payment_pk"]).encode('utf-8')).hexdigest()

    return {
        "template_group": settings.TEMPLATE_GROUP,
        "template_header_logo": TEMPLATE_HEADER_LOGO,
        "template_title": TEMPLATE_TITLE,
        'DEBUG': settings.DEBUG,
        'SYSTEM_NAME': settings.SYSTEM_NAME,
        'PUBLIC_URL': PUBLIC_URL,
        'TEMPLATE_GROUP': get_template_group(request), # Bad naming since we also have TEMPLATE_GROUP in settings however this one which always returns 'apiary'
        # may still be used in some places
        'APPLICATION_GROUP': 'apiary',
        'SUPPORT_EMAIL': settings.SUPPORT_EMAIL,
        'is_payment_admin': is_payment_officer,
        'build_tag': settings.BUILD_TAG,
        'KB_SERVER_URL': KB_SERVER_URL,
        'KB_BASEMAP_STREET_LAYER': KB_BASEMAP_STREET_LAYER,
        'KB_BASEMAP_SATELLITE_LAYER': KB_BASEMAP_SATELLITE_LAYER,
        'ledger_totals': lt,
        'LEDGER_UI_URL': f'{settings.LEDGER_UI_URL}',
        'GIT_COMMIT_HASH' : settings.GIT_COMMIT_HASH,
        "vue3_entry_script": settings.VUE3_ENTRY_SCRIPT,
        'LEDGER_SYSTEM_ID': f'{settings.LEDGER_SYSTEM_ID}',
        'DJANGO_SETTINGS': settings,
        'checkouthash' : checkouthash,
        'PRIVACY_POLICY_URL': settings.PRIVACY_POLICY_URL,
    }

import pytz
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from django.http.response import HttpResponse

from disturbance.components.main.models import ApplicationType, ApiaryGlobalSettings
from disturbance.components.proposals.models import (
    SiteCategory, ApiarySiteFeeType, 
    ApiarySiteFeeRemainder, ApiaryAnnualRentalFee, 
    ApiarySite
)
from disturbance.components.ap_payments.models import ApplicationFee, AnnualRentalFee, ApplicationFeeInvoice
from ledger_api_client.utils import (
    create_basket_session, create_checkout_session, calculate_excl_gst, 
    use_existing_basket_from_invoice
)
from ledger_api_client.ledger_models import Invoice

import logging

from disturbance.settings import DEBUG, PRODUCTION_EMAIL, ANNUAL_RENTAL_FEE_GST_EXEMPT

logger = logging.getLogger(__name__)


def get_session_application_invoice(session):
    """ Application Fee session ID """
    if 'das_app_invoice' in session:
        application_fee_id = session['das_app_invoice']
    else:
        raise Exception('Application not in Session')

    try:
        return ApplicationFee.objects.get(id=application_fee_id)
    except ApplicationFee.DoesNotExist:
        raise Exception('Application not found for application {}'.format(application_fee_id))


def set_session_application_invoice(session, application_fee):
    """ Application Fee session ID """
    session['das_app_invoice'] = application_fee.id
    session.modified = True


def delete_session_annual_rental_fee(session):
    """ Application Fee session ID """
    if 'annual_rental_fee' in session:
        del session['annual_rental_fee']
        session.modified = True


def set_session_invoice(session, invoice):
    session['invoice_reference'] = invoice.reference
    session.modified = True


class InvoiceReferenceNotInSettionException(Exception):
    pass


def get_session_invoice(session):
    if 'invoice_reference' in session:
        invoice_reference = session['invoice_reference']
    else:
        raise InvoiceReferenceNotInSettionException('AnnualRentalFee not in Session')

    try:
        return Invoice.objects.get(reference=invoice_reference)
    except Invoice.DoesNotExist:
        raise Exception('Invoice not found for the reference {}'.format(invoice_reference))


def delete_session_invoice(session):
    if 'invoice_reference' in session:
        del session['invoice_reference']
        session.modified = True


def set_session_annual_rental_fee(session, annual_rental_fee):
    session['annual_rental_fee'] = annual_rental_fee.id
    session.modified = True


def get_session_annual_rental_fee(session):
    if 'annual_rental_fee' in session:
        annual_rental_fee_id = session['annual_rental_fee']
    else:
        raise Exception('AnnualRentalFee not in Session')

    try:
        return AnnualRentalFee.objects.get(id=annual_rental_fee_id)
    except AnnualRentalFee.DoesNotExist:
        raise Exception('AnnualRentalFee not found for id {}'.format(annual_rental_fee_id))


def delete_session_application_invoice(session):
    """ Application Fee session ID """
    if 'das_app_invoice' in session:
        del session['das_app_invoice']
        session.modified = True


def get_session_site_transfer_application_invoice(session):
    """ Application Fee session ID """
    if 'site_transfer_app_invoice' in session:
        application_fee_id = session['site_transfer_app_invoice']
    else:
        raise Exception('Application not in Session')

    try:
        #return Invoice.objects.get(id=application_invoice_id)
        #return Proposal.objects.get(id=proposal_id)
        return ApplicationFee.objects.get(id=application_fee_id)
    except ApplicationFee.DoesNotExist:
        raise Exception('Application not found for application {}'.format(application_fee_id))


def set_session_site_transfer_application_invoice(session, application_fee):
    """ Application Fee session ID """
    session['site_transfer_app_invoice'] = application_fee.id
    session.modified = True


def delete_session_site_transfer_application_invoice(session):
    """ Application Fee session ID """
    if 'site_transfer_app_invoice' in session:
        del session['site_transfer_app_invoice']
        session.modified = True


def create_fee_lines_site_transfer(proposal):

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    line_items = []

    # Calculate total number of sites applied per category
    summary = {}
    for site_transfer_site in proposal.proposal_apiary.site_transfer_apiary_sites.all():
        if site_transfer_site.customer_selected:
            if site_transfer_site.apiary_site_on_approval.site_category.id in summary:
                summary[site_transfer_site.apiary_site_on_approval.site_category.id] += 1
            else:
                summary[site_transfer_site.apiary_site_on_approval.site_category.id] = 1

    # Calculate number of sites to calculate the fee
    for site_category_id, number_of_sites_applied in summary.items():
        site_category = SiteCategory.objects.get(id=site_category_id)
        application_price = site_category.retrieve_current_fee_per_site_by_type(ApiarySiteFeeType.FEE_TYPE_TRANSFER)
        line_item = {
            'ledger_description': 'Application Fee - {} - {} - {}'.format(now, proposal.lodgement_number, site_category.display_name),
            'oracle_code': proposal.application_type.oracle_code_application,
            'price_incl_tax': str(application_price),
            'price_excl_tax': str(application_price) if proposal.application_type.is_gst_exempt else str(calculate_excl_gst(application_price)),
            'quantity': number_of_sites_applied,
        }
        line_items.append(line_item)

    return line_items, None


def _get_site_fee_remainders(site_category, apiary_site_fee_type_name, applicant, proxy_applicant):
    # Retrieve sites left
    if not applicant and not proxy_applicant:
        # Should not reach here
        logger.error('No applicants are set to retrieve the remainders.')
        return None

    filter_site_category = Q(site_category=site_category)
    filter_site_fee_type = Q( apiary_site_fee_type=ApiarySiteFeeType.objects.get(name=apiary_site_fee_type_name))
    filter_applicant = Q(applicant=applicant)
    filter_proxy_applicant = Q(proxy_applicant=proxy_applicant)
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

    return site_fee_remainders


def _sum_apiary_sites_per_category(proposal_apiary):
    site_ids = []
    vacant_site_ids = []
    site_per_category_per_feetype = {
        SiteCategory.CATEGORY_SOUTH_WEST: {
            ApiarySiteFeeType.FEE_TYPE_APPLICATION: [],
            ApiarySiteFeeType.FEE_TYPE_RENEWAL: [],
        },
        SiteCategory.CATEGORY_REMOTE: {
            ApiarySiteFeeType.FEE_TYPE_APPLICATION: [],
            ApiarySiteFeeType.FEE_TYPE_RENEWAL: [],
        },
    }

    for relation in proposal_apiary.get_relations():
        if relation.for_renewal:
            fee_type = ApiarySiteFeeType.FEE_TYPE_RENEWAL
        else:
            fee_type = ApiarySiteFeeType.FEE_TYPE_APPLICATION

        site_per_category_per_feetype[relation.site_category_draft.name][fee_type].append(relation)

        if relation.apiary_site.is_vacant:
            vacant_site_ids.append(relation.apiary_site.id)
        else:
            site_ids.append(relation.apiary_site.id)

    return site_ids, vacant_site_ids, site_per_category_per_feetype


def _get_remainders_obj(number_of_sites_to_add_as_remainder, site_category_id, proposal, apiary_site_fee_type_name):
    # Add remainders
    remainders_arr = []

    for i in range(number_of_sites_to_add_as_remainder):
        site_to_be_added = {
            'site_category_id': site_category_id,
            'apiary_site_fee_type_name': apiary_site_fee_type_name,
            'applicant_id': proposal.applicant.id if proposal.applicant else None,
            'proxy_applicant_id': proposal.proxy_applicant.id if proposal.proxy_applicant else None,
        }
        remainders_arr.append(site_to_be_added)

    return remainders_arr


def get_db_operations(proposal):
    today_local = datetime.now(pytz.timezone(settings.TIME_ZONE)).date()
    MIN_NUMBER_OF_SITES_TO_RENEW = 5
    MIN_NUMBER_OF_SITES_TO_NEW = 5

    # Once payment success, data is updated based on this variable
    # This variable is stored in the session
    db_process_after_success = {
        'site_remainder_used': [],
        'site_remainder_to_be_added': [],
    }

    # Calculate total number of sites applied per category
    db_process_after_success['apiary_site_ids'], db_process_after_success['vacant_apiary_site_ids'], temp = _sum_apiary_sites_per_category(proposal.proposal_apiary)
    db_process_after_success['proposal_apiary_id'] = proposal.proposal_apiary.id

    # Calculate number of sites to calculate the fee
    for site_category_name, data_in_category in temp.items():
        site_category = SiteCategory.objects.get(name=site_category_name)

        for new_or_renewal, relations in data_in_category.items():
            min_num_of_sites_to_pay = None
            if not len(relations) > 0:
                # No apiary sites for this 'site_cateogyr' and 'new_or_renewal'
                continue

            site_fee_remainders = _get_site_fee_remainders(site_category, new_or_renewal, proposal.applicant, proposal.proxy_applicant)

            # Calculate deduction and set date_used field
            number_of_sites_after_deduction = len([relation for relation in relations if not relation.application_fee_paid])
            for site_left in site_fee_remainders:
                if number_of_sites_after_deduction == 0:
                    break
                number_of_sites_after_deduction -= 1
                site_remainder_used = {
                    'id': site_left.id,
                    'date_used': today_local.strftime('%Y-%m-%d')
                }
                db_process_after_success['site_remainder_used'].append(site_remainder_used)

            if new_or_renewal == ApiarySiteFeeType.FEE_TYPE_APPLICATION:
                min_num_of_sites_to_pay = MIN_NUMBER_OF_SITES_TO_NEW
            elif new_or_renewal == ApiarySiteFeeType.FEE_TYPE_RENEWAL:
                min_num_of_sites_to_pay = MIN_NUMBER_OF_SITES_TO_RENEW
            else:
                min_num_of_sites_to_pay = 5

            if min_num_of_sites_to_pay:
                quotient, remainder = divmod(number_of_sites_after_deduction, min_num_of_sites_to_pay)
                number_of_sites_calculate = quotient * min_num_of_sites_to_pay + min_num_of_sites_to_pay if remainder else quotient * min_num_of_sites_to_pay
                number_of_sites_to_add_as_remainder = number_of_sites_calculate - number_of_sites_after_deduction

                # Add remainders
                site_remainder_to_be_added = _get_remainders_obj(number_of_sites_to_add_as_remainder, site_category.id, proposal, new_or_renewal)
                db_process_after_success['site_remainder_to_be_added'].extend(site_remainder_to_be_added)

    return db_process_after_success


def create_fee_lines_apiary(proposal):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    today_local = datetime.now(pytz.timezone(settings.TIME_ZONE)).date()
    MIN_NUMBER_OF_SITES_TO_RENEW = 5
    MIN_NUMBER_OF_SITES_TO_NEW = 5
    line_items = []

    # Once payment success, data is updated based on this variable
    # This variable is stored in the session
    db_process_after_success = {
        'site_remainder_used': [],
        'site_remainder_to_be_added': [],
    }

    # Calculate total number of sites applied per category
    db_process_after_success['apiary_site_ids'], db_process_after_success['vacant_apiary_site_ids'], temp = _sum_apiary_sites_per_category(proposal.proposal_apiary)
    db_process_after_success['proposal_apiary_id'] = proposal.proposal_apiary.id

    # Calculate number of sites to calculate the fee
    for site_category_name, data_in_category in temp.items():
        site_category = SiteCategory.objects.get(name=site_category_name)

        for new_or_renewal, relations in data_in_category.items():
            if not len(relations) > 0:
                # No apiary sites for this 'site_cateogyr' and 'new_or_renewal'
                continue

            site_fee_remainders = _get_site_fee_remainders(site_category, new_or_renewal, proposal.applicant, proposal.proxy_applicant)

            # Calculate deduction and set date_used field
            number_of_sites_after_deduction = len([relation for relation in relations if not relation.application_fee_paid])
            for site_left in site_fee_remainders:
                if number_of_sites_after_deduction == 0:
                    break
                number_of_sites_after_deduction -= 1
                site_remainder_used = {
                    'id': site_left.id,
                    'date_used': today_local.strftime('%Y-%m-%d')
                }
                db_process_after_success['site_remainder_used'].append(site_remainder_used)

            if new_or_renewal == ApiarySiteFeeType.FEE_TYPE_APPLICATION:
                min_num_of_sites_to_pay = MIN_NUMBER_OF_SITES_TO_NEW
                ledger_desc = 'New Apiary Site Fee - {} - {} - {}'.format(now, proposal.lodgement_number, site_category.display_name)
            elif new_or_renewal == ApiarySiteFeeType.FEE_TYPE_RENEWAL:
                min_num_of_sites_to_pay = MIN_NUMBER_OF_SITES_TO_RENEW
                ledger_desc = 'Renewal Fee - {} - {} - {}'.format(now, proposal.lodgement_number, site_category.display_name)
            else:
                # Should not reach here
                min_num_of_sites_to_pay = 5
                ledger_desc = ''

            quotient, remainder = divmod(number_of_sites_after_deduction, min_num_of_sites_to_pay)
            number_of_sites_calculate = quotient * min_num_of_sites_to_pay + min_num_of_sites_to_pay if remainder else quotient * min_num_of_sites_to_pay
            number_of_sites_to_add_as_remainder = number_of_sites_calculate - number_of_sites_after_deduction
            application_price = site_category.retrieve_current_fee_per_site_by_type(new_or_renewal)

            # Avoid ledger error
            # ledger doesn't accept quantity=0). Alternatively, set quantity=1 and price=0
            if number_of_sites_calculate == 0:
                number_of_sites_calculate = len(relations)
                application_price = 0

            line_item = {
                'ledger_description': ledger_desc,
                'oracle_code': proposal.application_type.oracle_code_application,
                'price_incl_tax': str(application_price),
                'price_excl_tax': str(application_price) if proposal.application_type.is_gst_exempt else str(calculate_excl_gst(application_price)),
                'quantity': number_of_sites_calculate,
            }
            line_items.append(line_item)

            # Add remainders
            site_remainder_to_be_added = _get_remainders_obj(number_of_sites_to_add_as_remainder, site_category.id, proposal, new_or_renewal)
            db_process_after_success['site_remainder_to_be_added'].extend(site_remainder_to_be_added)

    return line_items, db_process_after_success


def create_fee_lines(proposal, invoice_text=None, vouchers=[], internal=False):
    """ Create the ledger lines - line item for application fee sent to payment system """

    db_processes_after_success = {}

    if proposal.application_type.name == ApplicationType.APIARY:
        line_items, db_processes_after_success = create_fee_lines_apiary(proposal)  # This function returns line items and db_processes as a tuple
    elif proposal.application_type.name == ApplicationType.SITE_TRANSFER:
        line_items, db_processes_after_success = create_fee_lines_site_transfer(proposal)  # This function returns line items and db_processes as a tuple
    else:
        now = datetime.now().strftime('%Y-%m-%d %H:%M')

        # Non 'Apiary' proposal
        application_price = proposal.application_type.application_fee
        line_items = [
            {
                'ledger_description': 'Application Fee - {} - {}'.format(now, proposal.lodgement_number),
                'oracle_code': proposal.application_type.oracle_code_application,
                'price_incl_tax':  str(application_price),
                'price_excl_tax':  str(application_price) if proposal.application_type.is_gst_exempt else str(calculate_excl_gst(application_price)),
                'quantity': 1,
            },
        ]

    logger.info('{}'.format(line_items))

    return line_items, db_processes_after_success


def checkout(
        request, 
        proposal, 
        lines, 
        return_url_ns='public_payment_success', 
        return_preload_url_ns='public_payment_success', 
        invoice_text=None, 
        vouchers=[], 
        proxy=False
    ):
    print("checkout")
    basket_params = {
        'products': lines,
        'vouchers': vouchers,
        'system': settings.PAYMENT_SYSTEM_ID,
        'custom_basket': True,
        'booking_reference': proposal.lodgement_number,
        'booking_reference_link': proposal.lodgement_number,
        'no_payment': False,
    }

    email_user_id = proposal.submitter_id
    basket_hash = create_basket_session(request, email_user_id, basket_params)

    external_url = settings.APIARY_EXTERNAL_URL if settings.APIARY_EXTERNAL_URL.startswith('http') else request.build_absolute_uri('/').rstrip('/')
    checkout_params = {
        'system': settings.PAYMENT_SYSTEM_ID,
        'fallback_url': request.build_absolute_uri('/'),
        'return_url': request.build_absolute_uri(reverse(return_url_ns,kwargs={"lodgement_number": proposal.lodgement_number})),
        'return_preload_url': external_url + reverse(return_preload_url_ns,kwargs={"lodgement_number": proposal.lodgement_number}),
        'force_redirect': True,
        'proxy': proxy,
        'invoice_text': invoice_text,
        'basket_owner': email_user_id,
        'session_type': 'ledger_api',
    }
    print(checkout_params['return_preload_url'])
    create_checkout_session(request, checkout_params)

    response = HttpResponse(
        "<script> window.location='" + reverse('ledgergw-payment-details') + "';</script> <a href='" + reverse(
            'ledgergw-payment-details'
            ) + "'> Redirecting please wait: " + reverse('ledgergw-payment-details') + "</a>"
        )

    return response


def calculate_total_annual_rental_fee(approval, period, sites_charged):
    if period[0] > period[1]:
        # Charge start date is after the charge end date
        raise ValidationError('Something wrong with the period to charge. Charge start date is after the charge end date')

    if approval.expiry_date < period[0]:
        # Check if the approval is valid
        raise ValidationError('This approval is/will be expired before the annual site fee period starts')

    if approval.no_annual_rental_fee_until:
        if approval.no_annual_rental_fee_until >= period[1]:
            # No fee charged
            return 0

    # Calculate charge start date taking into account the licence's start date
    invoice_period_start_date = approval.no_annual_rental_fee_until + timedelta(days=1) \
        if approval.no_annual_rental_fee_until and period[0] < (approval.no_annual_rental_fee_until + timedelta(days=1)) \
        else period[0]
    invoice_period_start_date = invoice_period_start_date if approval.start_date < invoice_period_start_date else approval.start_date

    # Calculate charge end date taking into account the licence's end date
    invoice_period_end_date = period[1] if period[1] <= approval.expiry_date else approval.expiry_date

    apiary_sites_charged = {}
    for my_site in sites_charged:
        if isinstance(my_site, ApiarySite):
            apiary_site = my_site
        else:
            apiary_site = ApiarySite.objects.get(id=my_site['id'])
        last_annual_rental_fee = AnnualRentalFee.objects.filter(approval=approval, annualrentalfeeapiarysite__apiary_site=apiary_site).order_by('-invoice_period_end_date').first()
        if last_annual_rental_fee:
            # There is at least one payment for this site
            if last_annual_rental_fee.invoice_period_end_date < invoice_period_end_date:
                # Partially paid somehow
                charge_start_date_for_this_site = last_annual_rental_fee.invoice_period_end_date + timedelta(days=1)
                charge_end_date_for_this_site = invoice_period_end_date
            else:
                # Already paid for this period for this apiary site
                continue
        else:
            # Calculate the number of days to be charged
            charge_start_date_for_this_site = invoice_period_start_date
            charge_end_date_for_this_site = invoice_period_end_date

        charge_period = (charge_start_date_for_this_site, charge_end_date_for_this_site)
        if charge_period in apiary_sites_charged:
            apiary_sites_charged[charge_period].append(apiary_site)
        else:
            apiary_sites_charged[charge_period] = [apiary_site]

    return apiary_sites_charged, (invoice_period_start_date, invoice_period_end_date)


def round_amount_according_to_env(amount):
    if not DEBUG and PRODUCTION_EMAIL:
        amount = round(amount, 2)  # Round to 2 decimal places
    else:
        # in Dev/UAT, avoid decimal amount, otherwise payment is declined
        amount = round(amount)
    return amount


def generate_line_items_for_annual_rental_fee(approval, today_now, period, apiary_sites_to_be_charged):
    oracle_code_obj = ApiaryGlobalSettings.objects.get(key=ApiaryGlobalSettings.KEY_ORACLE_CODE_APIARY_SITE_ANNUAL_RENTAL_FEE)
    num_of_days_in_year = 365

    # Retrieve summarised payment data per charge_period
    apiary_sites_charged, invoice_period = calculate_total_annual_rental_fee(approval, period, apiary_sites_to_be_charged)

    line_items = []

    if apiary_sites_charged:
        for charge_period, apiary_sites in apiary_sites_charged.items():
            if not len(apiary_sites):
                continue

            fees_applied = ApiaryAnnualRentalFee.get_fees_by_period(charge_period[0], charge_period[1])  # fee might be changed during the period, that's why retern value is an array

            amount_south_west_per_site = 0
            amount_remote_per_site = 0
            for fee_for_site in fees_applied:
                amount_south_west_per_site += fee_for_site.get('amount_south_west_per_year') * fee_for_site.get('num_of_days').days / num_of_days_in_year
                amount_remote_per_site += fee_for_site.get('amount_remote_per_year') * fee_for_site.get('num_of_days').days / num_of_days_in_year

            apiary_sites_by_category = {
                SiteCategory.CATEGORY_SOUTH_WEST: [],
                SiteCategory.CATEGORY_REMOTE: [],
            }
            for a_site in apiary_sites:
                if a_site.latest_approval_link.site_category.name == SiteCategory.CATEGORY_SOUTH_WEST:
                    apiary_sites_by_category[SiteCategory.CATEGORY_SOUTH_WEST].append(a_site)
                else:
                    apiary_sites_by_category[SiteCategory.CATEGORY_REMOTE].append(a_site)

            for category, apiary_sites in apiary_sites_by_category.items():
                if not len(apiary_sites):
                    continue
                amount_per_site = amount_south_west_per_site if category == SiteCategory.CATEGORY_SOUTH_WEST else amount_remote_per_site
                category_display = 'South West' if category == SiteCategory.CATEGORY_SOUTH_WEST else 'Remote'

                total_amount = amount_per_site * len(apiary_sites)
                total_amount = total_amount if total_amount >= 0 else 0
                total_amount = round_amount_according_to_env(total_amount)

                line_item = {}
                line_item['ledger_description'] = 'Annual Site Fee ({}): {}, Issued: {} {}, Period: {} to {}, Site(s): {}'.format(
                    category_display,
                    approval.lodgement_number,
                    today_now.strftime("%d/%m/%Y"),
                    today_now.strftime("%I:%M %p"),
                    charge_period[0].strftime("%d/%m/%Y"),
                    charge_period[1].strftime("%d/%m/%Y"),
                    ', '.join(['site: ' + str(site.id) for site in apiary_sites])
                )
                if len(line_item['ledger_description']) >= 250:
                    # description too long, shorten it
                    line_item['ledger_description'] = 'Annual Site Fee ({}): {}, Issued: {} {}, Period: {} to {}, Number of sites: {}'.format(
                        category_display,
                        approval.lodgement_number,
                        today_now.strftime("%d/%m/%Y"),
                        today_now.strftime("%I:%M %p"),
                        charge_period[0].strftime("%d/%m/%Y"),
                        charge_period[1].strftime("%d/%m/%Y"),
                        len(apiary_sites)
                    )

                line_item['oracle_code'] = oracle_code_obj.value
                line_item['price_incl_tax'] = total_amount
                line_item['price_excl_tax'] = total_amount if ANNUAL_RENTAL_FEE_GST_EXEMPT else calculate_excl_gst(total_amount)
                line_item['quantity'] = 1

                line_items.append(line_item)

    return line_items, apiary_sites_charged, invoice_period


def checkout_existing_invoice(request, invoice, return_url_ns='public_booking_success'):
    print("checkout_existing_invoice")
    basket, basket_hash = use_existing_basket_from_invoice(invoice.reference)
    external_url = settings.APIARY_EXTERNAL_URL if settings.APIARY_EXTERNAL_URL.startswith('http') else request.build_absolute_uri('/').rstrip('/')
    checkout_params = {
        'system': settings.PAYMENT_SYSTEM_ID,
        'fallback_url': request.build_absolute_uri('/'),
        'return_url': request.build_absolute_uri(reverse(return_url_ns)),
        'return_preload_url': external_url + reverse(return_url_ns),
        'force_redirect': True,
        'invoice_text': invoice.text,
    }
    
    if request.user.is_anonymous():
        # We need to determine the basket owner and set it to the checkout_params to proceed the payment
        annual_rental_fee = AnnualRentalFee.objects.filter(invoice_reference=invoice.reference)
        application_fee_invoice = ApplicationFeeInvoice.objects.filter(invoice_reference=invoice.reference)
        if annual_rental_fee:
            annual_rental_fee = annual_rental_fee[0]
            checkout_params['basket_owner'] = annual_rental_fee.approval.relevant_applicant_email_user.id
        else:
            # Should not reach here
            # At the moment, there should be only the 'annual rental fee' invoices for anonymous user
            pass

    create_checkout_session(request, checkout_params)

    # response = HttpResponseRedirect(reverse('checkout:index'))
    # use HttpResponse instead of HttpResponseRedirect - HttpResonseRedirect does not pass cookies which is important for ledger to get the correct basket
    response = HttpResponse(
        "<script> window.location='" + reverse('checkout:index') + "';</script> <a href='" + reverse(
            'checkout:index') + "'> Redirecting please wait: " + reverse('checkout:index') + "</a>")

    # inject the current basket into the redirect response cookies
    # or else, anonymous users will be directionless
    response.set_cookie(
        settings.OSCAR_BASKET_COOKIE_OPEN, basket_hash,
        max_age=settings.OSCAR_BASKET_COOKIE_LIFETIME,
        secure=settings.OSCAR_BASKET_COOKIE_SECURE, httponly=True
    )
    return response
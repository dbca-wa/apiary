from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import View, TemplateView
from django.db import transaction
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from datetime import datetime
from ledger_api_client.ledger_models import EmailUserRO as EmailUser

from disturbance.components.approvals.email import (
    get_value_of_annual_rental_fee_awaiting_payment_confirmation,
    send_annual_rental_fee_invoice
)
from disturbance.components.approvals.serializers import ApprovalLogEntrySerializer
from disturbance.components.proposals.models import (
    Proposal, ApiarySiteFeeRemainder,
    ApiarySiteFeeType, SiteCategory,
)
from disturbance.components.main.models import ApplicationType
from disturbance.components.organisations.models import Organisation
from disturbance.components.ap_payments.confirmation_pdf import create_confirmation_pdf_bytes
from disturbance.components.proposals.utils import proposal_submit_apiary
from disturbance.components.ap_payments.email import (
    send_application_fee_invoice_apiary_email_notification,
)
from disturbance.components.ap_payments.utils import (
    checkout,
    create_fee_lines,
    get_session_application_invoice,
    set_session_application_invoice,
    get_db_operations,
    set_session_site_transfer_application_invoice,
    delete_session_site_transfer_application_invoice, set_session_annual_rental_fee, get_session_annual_rental_fee,
    delete_session_annual_rental_fee, round_amount_according_to_env, set_session_invoice,
    get_session_invoice, delete_session_invoice, InvoiceReferenceNotInSettionException,
)

from disturbance.components.ap_payments.models import ApplicationFee, ApplicationFeeInvoice, AnnualRentalFee
from ledger_api_client.utils import get_invoice_properties, validate_booking_and_invoice_references
from decimal import Decimal
import requests

from ledger_api_client.ledger_models import Invoice, Basket
from disturbance.helpers import is_internal, is_in_organisation_contacts
from disturbance.context_processors import apiary_url
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers

from django.conf import settings

import logging
logger = logging.getLogger(__name__)

#TODO on-cleanup - this is not used, determine if needed or not (appears to have been a partially completed addition from some number of years ago that was never fully implemented)
class AnnualRentalFeeView(TemplateView):
    def get_object(self):
        return get_object_or_404(AnnualRentalFee, id=self.kwargs['annual_rental_fee_id'])

    def restore_original_format(self, lines):
        for line in lines:
            for key in line:
                if key in ('price_incl_tax', 'price_excl_tax') and isinstance(line[key], (str, bytes)):  # Python 3 renamed the unicode type to str, the old str type has been replaced by bytes
                    amount_f = float(line[key])  # string to float
                    round_f = round_amount_according_to_env(amount_f)
                    decimal_f = Decimal(str(round_f))  # Generate Decimal with 2 decimal places string
                    line[key] = decimal_f
        return lines

    def get(self, request, *args, **kwargs):
        annual_rental_fee = self.get_object()

        try:
            with transaction.atomic():
                set_session_annual_rental_fee(request.session, annual_rental_fee)
                invoice = Invoice.objects.get(reference=annual_rental_fee.invoice_reference)

                proposal = annual_rental_fee.current_proposal

                lines, _ = create_fee_lines(proposal)

                checkout_response = checkout(
                        request,
                        proposal,
                        lines,
                        return_url_ns='invoice_payment_success',
                        return_preload_url_ns='invoice_payment_success',
                        invoice_text=invoice.text,
                    )

                logger.info('{} built payment line item {} for Annual Site Fee and handing over to payment gateway'.format(
                    'User {} with id {}'.format(
                        request.user.get_full_name(), request.user.id
                    ), annual_rental_fee.approval.lodgement_number
                ))
                return checkout_response

        except Exception as e:
            logger.error('Error Creating Annual Site Fee: {}'.format(e))
            raise

#TODO on-cleanup - this appears to be no longer used, determine if needed or not 
class InvoicePaymentView(TemplateView):

    def get_object(self):
        return get_object_or_404(Invoice, reference=self.kwargs['invoice_reference'])

    def post(self, request, *args, **kwargs):
        invoice = self.get_object()
        
        try:
            with transaction.atomic():

                proposal = Proposal.objects.get(lodgement_number=invoice.reference)
                lines, _ = create_fee_lines(proposal)

                set_session_invoice(request.session, invoice)

                checkout_response = checkout(
                        request,
                        proposal,
                        lines,
                        return_url_ns='invoice_payment_success',
                        return_preload_url_ns='invoice_payment_success',
                        invoice_text=invoice.text,
                    )

                if request.user.id:
                    logger.info('{} handing over to payment gateway for the invoice: {}'.format(
                        'User {} with id {}'.format(request.user.get_full_name(), request.user.id),
                        invoice.reference
                    ))
                else:
                    logger.info('Anonymous user handing over to payment gateway for the invoice: {}'.format(invoice.reference))

                return checkout_response

        except Exception as e:
            logger.error('Error Creating Annual Site Fee: {}'.format(e))
            raise


class ApplicationFeeView(TemplateView):
    template_name = 'disturbance/payment/success_fee.html'

    def get_object(self):
        return get_object_or_404(Proposal, id=self.kwargs['proposal_pk'])

    def post(self, request, *args, **kwargs):

        proposal = self.get_object()
        user = request.user
        try:
            user_orgs = [org.id for org in user.disturbance_organisations.all()]
            if not (
                is_internal(self.request) or
                proposal.applicant_id in user_orgs or proposal.submitter == user
            ):
                raise PermissionDenied
        except:
            raise

        application_fee = ApplicationFee.objects.create(proposal=proposal, created_by=request.user, payment_type=ApplicationFee.PAYMENT_TYPE_TEMPORARY)
        print('application_fee:',application_fee)
        try:
            with transaction.atomic():
                if proposal.application_type.name == ApplicationType.SITE_TRANSFER:
                    set_session_site_transfer_application_invoice(request.session, application_fee)
                else:
                    set_session_application_invoice(request.session, application_fee)
                lines, _ = create_fee_lines(proposal)

                if proposal.application_type.name == ApplicationType.SITE_TRANSFER:
                    checkout_response = checkout(
                        request,
                        proposal,
                        lines,
                        return_url_ns='site_transfer_fee_success',
                        return_preload_url_ns='fee_success_preload',
                        invoice_text='Site Transfer Application Fee'
                    )
                else:
                    checkout_response = checkout(
                        request,
                        proposal,
                        lines,
                        return_url_ns='fee_success',
                        return_preload_url_ns='fee_success_preload',
                        invoice_text='Application Fee'
                    )

                request.session["payment_pk"] = proposal.pk
                
                logger.info('{} built payment line item {} for Application Fee and handing over to payment gateway'.format('User {} with id {}'.format(proposal.submitter.get_full_name(),proposal.submitter.id), proposal.id))
                return checkout_response

        except Exception as e:
            logger.error('Error Creating Application Fee: {}'.format(e))
            if application_fee:
                application_fee.delete()
            raise


class SiteTransferApplicationFeeSuccessView(TemplateView):
    template_name = 'disturbance/payment/success_fee.html'

    def valid_token_payment_session(self, request, invoice_reference):
        if 'token_payment_session' in request.session:
            basket = Basket.objects.filter(status='Submitted', id=request.session['token_payment_session']).order_by('-id').first()
            del request.session['token_payment_session']
            return validate_booking_and_invoice_references(basket.booking_reference, invoice_reference)

    def get(self, request, lodgement_number, *args, **kwargs):
        print (" SITE TRANSFER APPLICATION FEE SUCCESS VIEW ")
        proposal = None
        submitter = None
        invoice = None
        try:
            proposal = Proposal.objects.get(lodgement_number=lodgement_number)
            print("proposal:",proposal)
        except Exception as e:
            print(e)
            return redirect('home')

        try:
            application_fee = ApplicationFee.objects.filter(proposal=proposal).order_by('id').last()
            try:
                if proposal.applicant:
                    recipient = proposal.applicant.email
                elif proposal.proxy_applicant:
                    recipient = proposal.proxy_applicant.email
                else:
                    recipient = proposal.submitter.email
            except:
                recipient = proposal.submitter.email
            submitter = proposal.submitter

            fee_inv = ApplicationFeeInvoice.objects.filter(application_fee=application_fee).order_by('id').last()
            if fee_inv and fee_inv.invoice_reference:
                invoice_ref = fee_inv.invoice_reference
                invoice = Invoice.objects.filter(reference=invoice_ref).order_by('id').last()

            user = request.user
            try:
                try:
                    user_orgs = [org.id for org in user.disturbance_organisations.all()]
                except:
                    user_orgs = []
                if not (
                    is_internal(self.request) or
                    proposal.applicant_id in user_orgs or proposal.submitter == user or
                    self.valid_token_payment_session(request, invoice_ref)
                ):
                    raise PermissionDenied
            except Exception as e:
                print(e)
                return redirect('home')

            if application_fee and application_fee.payment_type == ApplicationFee.PAYMENT_TYPE_TEMPORARY:
                try:
                    inv = Invoice.objects.get(reference=invoice_ref)
                except Invoice.DoesNotExist:
                    logger.error('{} tried paying an application fee with an incorrect invoice'.format('User {} with id {}'.format(proposal.submitter.get_full_name(), proposal.submitter.id) if proposal.submitter else 'An anonymous user'))
                    return redirect('external-proposal-detail', args=(proposal.id,))
                if inv.system not in ['0517']:
                    logger.error('{} tried paying an application fee with an invoice from another system with reference number {}'.format('User {} with id {}'.format(proposal.submitter.get_full_name(), proposal.submitter.id) if proposal.submitter else 'An anonymous user',inv.reference))
                    return redirect('external-proposal-detail', args=(proposal.id,))

                if fee_inv:
                    application_fee.payment_type = ApplicationFee.PAYMENT_TYPE_INTERNET
                    application_fee.expiry_time = None

                    invoice_properties = get_invoice_properties(invoice.id)
                    if proposal and (invoice_properties['data']['invoice']['payment_status'] == 'paid' or invoice_properties['data']['invoice']['payment_status'] == 'over_paid'):
                        if isinstance(proposal.fee_invoice_references, list):
                            proposal.fee_invoice_references.append(invoice_ref)
                        else:
                            proposal.fee_invoice_references = [invoice_ref,]
                        proposal.save()
                        proposal_submit_apiary(proposal, request)
                    else:
                        logger.error('Invoice payment status is {}'.format(invoice_properties['data']['invoice']['payment_status']))
                        raise

                    application_fee.save()
                    request.session['site_transfer_last_app_invoice'] = application_fee.id
                    delete_session_site_transfer_application_invoice(request.session)

                    send_application_fee_invoice_apiary_email_notification(request, proposal, invoice, recipients=[recipient])

                    context = {
                        'proposal': proposal,
                        'submitter': submitter,
                        'fee_invoice': invoice
                    }
                    return render(request, self.template_name, context)

        except Exception as e:
            print(e)
            if ('site_transfer_last_app_invoice' in request.session) and ApplicationFee.objects.filter(id=request.session['site_transfer_last_app_invoice']).exists():
                application_fee = ApplicationFee.objects.get(id=request.session['site_transfer_last_app_invoice'])
                proposal = application_fee.proposal
                user = request.user
                try:
                    try:
                        user_orgs = [org.id for org in user.disturbance_organisations.all()]
                    except:
                        user_orgs = []
                    if not (
                        is_internal(self.request) or
                        proposal.applicant_id in user_orgs or proposal.submitter == user
                    ):
                        raise PermissionDenied
                except Exception as e:
                    print(e)
                    return redirect('home')         
                
                try:
                    if proposal.applicant:
                        recipient = proposal.applicant.email
                    elif proposal.proxy_applicant:
                        recipient = proposal.proxy_applicant.email
                    else:
                        recipient = proposal.submitter.email
                except:
                    recipient = proposal.submitter.email
                submitter = proposal.submitter

                if ApplicationFeeInvoice.objects.filter(application_fee=application_fee).count() > 0:
                    afi = ApplicationFeeInvoice.objects.filter(application_fee=application_fee)
                    invoice = afi[0]
            else:
                return redirect('home')
        context = {
            'proposal': proposal,
            'submitter': submitter,
            'fee_invoice': invoice
        }
        return render(request, self.template_name, context)

#TODO on-cleanup - this appears to be no longer used, determine if needed or not 
class InvoicePaymentSuccessView(TemplateView):
    template_name = 'disturbance/payment/invoice_payment_success.html'

    def get(self, request, *args, **kwargs):
        invoice = None

        try:
            invoice = get_session_invoice(request.session)  # When accessed 2nd time, this raises an Exception
            request.session['last_invoice_reference'] = invoice.reference
            delete_session_invoice(request.session)

            context = {}
            return render(request, self.template_name, context)

        except Invoice.DoesNotExist:
            logger.error('Invoice reference:{} not found in the database'.format(request.session['last_invoice_reference']))
            return redirect('home')

        except InvoiceReferenceNotInSettionException as e:
            if 'last_invoice_reference' in request.session and Invoice.objects.filter(reference=request.session['last_invoice_reference']).exists():
                invoice = Invoice.objects.get(reference=request.session['last_invoice_reference'])
                del request.session['last_invoice_reference']
                request.session.modified = True

                annual_rental_fee = AnnualRentalFee.objects.filter(invoice_reference=invoice.reference)
                application_fee_invoice = ApplicationFeeInvoice.objects.filter(invoice_reference=invoice.reference)
                if annual_rental_fee:
                    # This invoice is issued for the Annual Site Fee
                    annual_rental_fee = annual_rental_fee.first()
                    can_access_invoice, to_email_addresses = AnnualRentalFeeSuccessView.send_invoice_mail(annual_rental_fee, invoice, request)
                    self.template_name = 'disturbance/payment/annual_rental_fee_success.html'

                    context = {
                        'invoice_reference': invoice.reference,
                        'to_email_address': to_email_addresses,
                        'can_access_invoice': can_access_invoice,
                    }
                    return render(request, self.template_name, context)
                else:
                    # Should not reach here,
                    # At the moment, invoice for the annual rental fee is the only the invoice issued before actual payments
                    return redirect('home')
            else:
                return redirect('home')
        except Exception as e:
            logger.error('Error after payment success: {}'.format(e))
            return redirect('home')

#TODO on-cleanup - this is not used, determine if needed or not
class AnnualRentalFeeSuccessView(TemplateView):
    template_name = 'disturbance/payment/annual_rental_fee_success.html'

    def get(self, request, *args, **kwargs):
        invoice = None

        try:
            # When accessed first time, there is a annual_rental_fee in the session which was set at AnnualRentalFeeView()
            # but when accessed sencond time, it is deleted therefore raise an error.
            annual_rental_fee = get_session_annual_rental_fee(request.session)

            # if self.request.user.is_authenticated:
            #     basket = Basket.objects.filter(status='Submitted', owner=request.user).order_by('-id')[:1]
            # else:
            #     pass

            # order = Order.objects.get(basket=basket[0])
            invoice = Invoice.objects.get(reference=annual_rental_fee.invoice_reference)
            # annual_rental_fee.invoice_reference = invoice.reference
            # annual_rental_fee.save()

            request.session['last_annual_rental_fee_id'] = annual_rental_fee.id
            delete_session_annual_rental_fee(request.session)

            can_access_invoice, to_email_addresses = AnnualRentalFeeSuccessView.send_invoice_mail(annual_rental_fee, invoice, request)

            context = {
                'invoice_reference': annual_rental_fee.invoice_reference,
                'to_email_address': to_email_addresses,
                'can_access_invoice': can_access_invoice,
            }
            return render(request, self.template_name, context)

        except Exception as e:
            if 'last_annual_rental_fee_id' in request.session and AnnualRentalFee.objects.filter(id=request.session['last_annual_rental_fee_id']).exists():
                annual_rental_fee = AnnualRentalFee.objects.get(id=request.session['last_annual_rental_fee_id'])
                del request.session['last_annual_rental_fee_id']
                request.session.modified = True

                #TODO on cleanup: review, remove/adjust (old comment) Display success screen
                to_email_addresses = annual_rental_fee.approval.relevant_applicant.email
                can_access_invoice = False
                if request.user == annual_rental_fee.approval.relevant_applicant or \
                        annual_rental_fee.approval.applicant in request.user.disturbance_organisations.all():
                    can_access_invoice = True

                context = {
                    'invoice_reference': annual_rental_fee.invoice_reference,
                    'to_email_address': to_email_addresses,
                    'can_access_invoice': can_access_invoice,
                }
                return render(request, self.template_name, context)
            else:
                return redirect('home')

        except AnnualRentalFee.DoesNotExist:
            logger.error('AnnualRentalFee id:{} not found in the database'.format(request.session['last_annual_rental_fee_id']))
            return redirect('home')

    @staticmethod
    def send_invoice_mail(annual_rental_fee, invoice, request):
        # Send invoice
        to_email_addresses = annual_rental_fee.approval.relevant_applicant.email
        email_data = send_annual_rental_fee_invoice(annual_rental_fee.approval, invoice, [to_email_addresses, ])

        # Add comms log
        email_data['approval'] = u'{}'.format(annual_rental_fee.approval.id)
        serializer = ApprovalLogEntrySerializer(data=email_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Check if the request.user can access the invoice
        can_access_invoice = False
        if not request.user.is_anonymous():
            if request.user == annual_rental_fee.approval.relevant_applicant or \
                    annual_rental_fee.approval.applicant in request.user.disturbance_organisations.all():
                can_access_invoice = True

        return can_access_invoice, to_email_addresses


def adjust_db_operations(db_operations):

    if not db_operations:
        return        
    # Perform database operations to remove and/or store site remainders
    # site remainders used
    for item in db_operations['site_remainder_used']:
        site_remainder = ApiarySiteFeeRemainder.objects.get(id=item['id'])
        site_remainder.date_used = datetime.strptime(item['date_used'], '%Y-%m-%d')
        site_remainder.save()
    # site remainders added
    for item in db_operations['site_remainder_to_be_added']:
        apiary_site_fee_type = ApiarySiteFeeType.objects.get(name=item['apiary_site_fee_type_name'])
        site_category = SiteCategory.objects.get(id=item['site_category_id'])
        # date_expiry = datetime.strptime(item['date_expiry'], '%Y-%m-%d')
        applicant = Organisation.objects.get(id=item['applicant_id']) if item['applicant_id'] else None
        proxy_applicant = EmailUser.objects.get(id=item['proxy_applicant_id']) if item[
            'proxy_applicant_id'] else None
        site_remainder = ApiarySiteFeeRemainder.objects.create(
            site_category=site_category,
            apiary_site_fee_type=apiary_site_fee_type,
            applicant=applicant,
            proxy_applicant=proxy_applicant,
        )

class ApplicationFeeSuccessViewPreload(APIView):

    permission_classes = [AllowAny] 
    """ NOTE this endpoint must be openly accessible for payment notification
        while not ideal this should be okay provided:
            it only runs submissions and sends emails as needed (i.e. once assuming success on the first try)
            validates that payment has in fact been taken before running submissions
            does not return anything substantial in the response

        Currently this function if regulated, so that it does not run more than once, by checking:
            application_fee.payment_type == ApplicationFee.PAYMENT_TYPE_TEMPORARY

        TODO consider an allowed ip range so only specific services can access this endpoint
    """
    def get(self, request, lodgement_number, format=None):
        print("ApplicationFeeSuccessViewPreload")
        invoice_ref = request.GET.get('invoice')

        try:
            proposal = Proposal.objects.get(lodgement_number=lodgement_number)
            print("proposal:",proposal)
        except Exception as e:
            print(e)
            return redirect('home')

        if not validate_booking_and_invoice_references(proposal.lodgement_number, invoice_ref):
            raise serializers.ValidationError(f"Invoice: {invoice_ref} and Booking Reference: {proposal.lodgement_number} are not part of the same order/basket.")

        application_fee = ApplicationFee.objects.filter(proposal=proposal).order_by('id').last()
        print("af application fee",application_fee)
        if not application_fee:
            print("application fee for proposal does not exist")
            return redirect('home')
        
        Invoice.objects.filter(reference=invoice_ref).order_by('id').last()
        fee_inv, created = ApplicationFeeInvoice.objects.get_or_create(application_fee=application_fee, invoice_reference=invoice_ref)

        if fee_inv and fee_inv.invoice_reference:
            invoice_ref = fee_inv.invoice_reference
            invoice = Invoice.objects.filter(reference=invoice_ref).order_by('id').last()

        proposal = application_fee.proposal
        if proposal.application_type.name == ApplicationType.APIARY:
            db_operations = get_db_operations(proposal)
        else:
            db_operations = None

        if invoice and application_fee.payment_type == ApplicationFee.PAYMENT_TYPE_TEMPORARY:
            if fee_inv:
                application_fee.payment_type = ApplicationFee.PAYMENT_TYPE_INTERNET
                application_fee.expiry_time = None

                invoice_properties = get_invoice_properties(invoice.id)
                if (
                    proposal and invoice_properties['data'] and 
                    invoice_properties['data']['invoice'] and 
                    (
                        invoice_properties['data']['invoice']['payment_status'] == 'paid' 
                        or invoice_properties['data']['invoice']['payment_status']  == 'over_paid'
                    )
                ):
                    if isinstance(proposal.fee_invoice_references, list):
                        proposal.fee_invoice_references.append(invoice_ref)
                    else:
                        proposal.fee_invoice_references = [invoice_ref,]
                    proposal.save()
                    proposal_submit_apiary(proposal, request)

                    if proposal.proposal_apiary:
                        proposal_apiary = proposal.proposal_apiary
                        proposal_apiary.post_payment_success()

                    adjust_db_operations(db_operations)
                else:
                    logger.error('Invoice payment status is {}'.format(invoice_properties['data']['invoice']['payment_status'] if invoice_properties['data'] and invoice_properties['data']['invoice'] else "not available"))
                    raise
                
                recipient = None
                if proposal.applicant:
                    recipient = proposal.applicant.email
                elif proposal.proxy_applicant:
                    recipient = proposal.proxy_applicant.email
                elif proposal.submitter:
                    recipient = proposal.submitter.email

                application_fee.save()
                if recipient:
                    send_application_fee_invoice_apiary_email_notification(request, proposal, invoice, recipients=[recipient])

        return Response(status=status.HTTP_200_OK)


class ApplicationFeeSuccessView(TemplateView):
    template_name = 'disturbance/payment/success_fee.html'

    def valid_token_payment_session(self, request, invoice_reference):
        if 'token_payment_session' in request.session:
            basket = Basket.objects.filter(status='Submitted', id=request.session['token_payment_session']).order_by('-id').first()
            del request.session['token_payment_session']
            return validate_booking_and_invoice_references(basket.booking_reference, invoice_reference)

    def get(self, request, *args, **kwargs):
        print("ApplicationFeeSuccessView")
        fee_inv = None
        invoice = None
        submitter = None

        if 'token_payment_session' in request.session:
            invoice_ref = request.GET.get("invoice", "")
            fee_inv = ApplicationFeeInvoice.objects.filter(invoice_reference=invoice_ref).order_by('id').last()
            application_fee = fee_inv.application_fee
            submitter = proposal.submitter
        else:
            # Get application invoice from session
            application_fee = get_session_application_invoice(request.session)
            proposal = application_fee.proposal
            submitter = proposal.submitter
            fee_inv = ApplicationFeeInvoice.objects.filter(application_fee=application_fee).order_by('id').last()
            invoice_ref = fee_inv.invoice_reference

        user = request.user
        try:
            try:
                user_orgs = [org.id for org in user.disturbance_organisations.all()]
            except:
                user_orgs = []
            if not (
                is_internal(self.request) or
                proposal.applicant_id in user_orgs or proposal.submitter == user or
                self.valid_token_payment_session(request, invoice_ref)
            ):
                raise PermissionDenied
        except Exception as e:
            print(e)
            return redirect('home')

        if application_fee and application_fee.payment_type == ApplicationFee.PAYMENT_TYPE_TEMPORARY:
            # The preload callback (ApplicationFeeSuccessViewPreload) is called server-side by the
            # Ledger Gateway. If it did not run (e.g. APIARY_EXTERNAL_URL not configured so the
            # callback URL was unreachable), we handle the submission here as a fallback.
            if fee_inv and fee_inv.invoice_reference:
                # Preload already ran or invoice was created by another path — verify and submit.
                invoice_ref = fee_inv.invoice_reference
                invoice = Invoice.objects.filter(reference=invoice_ref).order_by('id').last()
                if invoice:
                    invoice_properties = get_invoice_properties(invoice.id)
                    if (
                        invoice_properties.get('data') and
                        invoice_properties['data'].get('invoice') and
                        invoice_properties['data']['invoice'].get('payment_status') in ('paid', 'over_paid')
                    ):
                        if isinstance(proposal.fee_invoice_references, list):
                            proposal.fee_invoice_references.append(invoice_ref)
                        else:
                            proposal.fee_invoice_references = [invoice_ref]
                        proposal.save()
                        proposal_submit_apiary(proposal, request)
                        if proposal.proposal_apiary:
                            proposal.proposal_apiary.post_payment_success()
                        db_operations = get_db_operations(proposal)
                        adjust_db_operations(db_operations)
                        application_fee.payment_type = ApplicationFee.PAYMENT_TYPE_INTERNET
                        application_fee.expiry_time = None
                        application_fee.save()
            else:
                # Preload never ran and no invoice recorded — this happens when APIARY_EXTERNAL_URL
                # is not set and process-zero was used for a zero-amount fee.
                # Verify the fee is truly zero before submitting without an invoice.
                try:
                    lines, db_operations = create_fee_lines(proposal)
                    total = sum(
                        Decimal(str(line.get('price_incl_tax', 0))) * line.get('quantity', 1)
                        for line in lines
                    )
                    if total == 0:
                        proposal_submit_apiary(proposal, request)
                        if proposal.proposal_apiary:
                            proposal.proposal_apiary.post_payment_success()
                        adjust_db_operations(db_operations)
                        application_fee.payment_type = ApplicationFee.PAYMENT_TYPE_INTERNET
                        application_fee.expiry_time = None
                        application_fee.save()
                    else:
                        logger.error(
                            'ApplicationFeeSuccessView: preload not called and fee is non-zero '
                            '(total={}) for proposal {}. Cannot submit without invoice verification.'.format(
                                total, proposal.lodgement_number
                            )
                        )
                except Exception as e:
                    logger.error('ApplicationFeeSuccessView: error in zero-fee fallback for {}: {}'.format(
                        proposal.lodgement_number, e
                    ))

        context = {
            'proposal': proposal,
            'submitter': submitter,
            'fee_invoice': fee_inv
        }
        return render(request, self.template_name, context)

#TODO on-cleanup - this is not used, determine if needed or not
class AwaitingPaymentPDFView(View):
    def get(self, request, *args, **kwargs):
        annual_rental_fee = get_object_or_404(AnnualRentalFee, id=self.kwargs['annual_rental_fee_id'])
        response = HttpResponse(content_type='application/pdf')
        response.write(get_value_of_annual_rental_fee_awaiting_payment_confirmation(annual_rental_fee))
        return response


class InvoicePDFView(View):
    def get(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, reference=self.kwargs['reference'])
        api_key = settings.LEDGER_API_KEY     

        if not self.request or not isinstance(self.request.user, EmailUser):
            raise PermissionDenied

        try:
            # Assume the invoice has been issued for the application(proposal)
            proposal = Proposal.objects.get(fee_invoice_references__contains=[invoice.reference])

            if proposal.relevant_applicant_type == 'organisation':
                organisation = proposal.applicant
                if self.check_owner(organisation):
                    response = HttpResponse(content_type='application/pdf')
                    url = settings.LEDGER_API_URL+'/ledgergw/invoice-pdf/'+api_key+'/' + invoice.reference
                    invoice_pdf = requests.get(url=url)
                    response.write(invoice_pdf)
                    return response
                raise PermissionDenied
            else:
                if self.check_individual_owner(proposal):
                    response = HttpResponse(content_type='application/pdf')
                    url = settings.LEDGER_API_URL+'/ledgergw/invoice-pdf/'+api_key+'/' + invoice.reference
                    invoice_pdf = requests.get(url=url)
                    response.write(invoice_pdf)
                    return response
                raise PermissionDenied
        #TODO on-cleanup remove if not needed, secure if needed
        #except Proposal.DoesNotExist:
        #    # The invoice might be issued for the annual site fee
        #    annual_rental_fee = AnnualRentalFee.objects.get(invoice_reference=invoice.reference)
        #    approval = annual_rental_fee.approval
        #    response = HttpResponse(content_type='application/pdf')
        #    url = settings.LEDGER_API_URL+'/ledgergw/invoice-pdf/'+api_key+'/' + invoice.reference
        #    invoice_pdf = requests.get(url=url)
        #    response.write(invoice_pdf)
        #    return response
        except:
            raise

    def get_object(self):
        return get_object_or_404(Invoice, reference=self.kwargs['reference'])

    def check_owner(self, organisation):
        return is_in_organisation_contacts(self.request, organisation) or is_internal(self.request) or self.request.user.is_superuser

    def check_individual_owner(self,proposal):
        if not self.request or not self.request.user:
            return False

        return (
            proposal.proxy_applicant == self.request.user if proposal.relevant_applicant_type == 'proxy' else proposal.submitter == self.request.user
        ) or is_internal(self.request) or self.request.user.is_superuser


class ConfirmationPDFView(View):
    def get(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, reference=self.kwargs['reference'])
        # proposal = Proposal.objects.get(fee_invoice_reference=invoice.reference)
        proposal = Proposal.objects.get(fee_invoice_references__contains=[invoice.reference])
        application_fee = proposal.application_fees.last()

        organisation = proposal.applicant.organisation.organisation_set.all()[0]
        if self.check_owner(organisation):
            response = HttpResponse(content_type='application/pdf')
            response.write(create_confirmation_pdf_bytes('confirmation.pdf',invoice, application_fee))
            return response
        raise PermissionDenied

    def get_object(self):
        return  get_object_or_404(Invoice, reference=self.kwargs['reference'])

    def check_owner(self, organisation):
        return is_in_organisation_contacts(self.request, organisation) or is_internal(self.request) or self.request.user.is_superuser

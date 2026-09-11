import io
import logging
import os

from django.conf import settings
from docx.shared import Mm
from docxtpl import DocxTemplate, InlineImage, R
from rest_framework.exceptions import ValidationError
from unoserver.client import UnoClient

from disturbance.components.main.models import ApiaryGlobalSettings

logger = logging.get_logger(__name__)


def create_apiary_licence_pdf_contents(approval, proposal, copied_to_permit, site_transfer_preview=None):
    from disturbance.components.approvals.serializers import ApprovalSerializerForLicenceDoc

    # 1. Fetch the docx template
    licence_template = ApiaryGlobalSettings.objects.filter(
        key=ApiaryGlobalSettings.KEY_APIARY_LICENCE_TEMPLATE_FILE
    ).first()

    if licence_template and licence_template._file:
        path_to_template = licence_template._file.path
    else:
        path_to_template = os.path.join(
            settings.BASE_DIR, "disturbance", "static", "disturbance", "apiary_authority_permit_template_v3.docx"
        )

    doc = DocxTemplate(path_to_template)
    path_to_image = os.path.join(settings.BASE_DIR, "disturbance", "static", "disturbance", "img", "dbca-logo.jpg")

    # 2. Serialize and build template context
    serializer_context = {
        "approver_id": approval.approver_id,
        "site_transfer_preview": site_transfer_preview,
    }
    context = ApprovalSerializerForLicenceDoc(approval, context=serializer_context).data
    context.update(
        {
            "dbca_logo": InlineImage(doc, image_descriptor=path_to_image, width=Mm(135), height=Mm(20)),
            "page_break": R("\f"),
        }
    )

    # 3. Render DOCX template in memory
    doc.render(context)

    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_bytes = doc_io.getvalue()

    # 4. Convert to PDF with graceful error handling
    try:
        client = UnoClient(server="127.0.0.1", port=2002)
        pdf_bytes = client.convert(indata=doc_bytes, convert_to="pdf")
    except (ConnectionRefusedError, OSError) as e:
        logger.error(
            "Unoserver connection failed on 127.0.0.1:2002 for Approval ID %s: %s",
            approval.id,
            e,
            exc_info=True,
        )
        raise ValidationError(
            "The document conversion service (Unoserver) is currently unreachable. "
            "Please try again or contact IT support if the problem persists."
        )
    except Exception as e:
        logger.error(
            "Unexpected error during PDF generation for Approval ID %s: %s",
            approval.id,
            e,
            exc_info=True,
        )
        raise ValidationError(f"An unexpected error occurred while generating the licence PDF: {str(e)}")

    return pdf_bytes

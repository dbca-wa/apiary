from django.db import transaction
from django.db.models import Q
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from rest_framework import mixins, serializers, status, views, viewsets
from rest_framework.decorators import action, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from disturbance.components.main.utils import (
    get_template_group,
)
from disturbance.components.organisations.models import (
    ApiaryOrganisationAccessGroup,
    Organisation,
    OrganisationAccessGroup,
    OrganisationContact,
    OrganisationRequest,
    OrganisationRequestUserAction,
)
from disturbance.components.organisations.permissions import (
    InternalOrganisationPermission,
    OrganisationRequestAssessorPermission,
)
from disturbance.components.organisations.serializers import (
    MyOrganisationsSerializer,
    OrganisationActionSerializer,
    OrganisationCheckExistSerializer,
    OrganisationCheckSerializer,
    OrganisationCommsSerializer,
    OrganisationContactSerializer,
    OrganisationLogEntrySerializer,
    OrganisationPinCheckSerializer,
    OrganisationRequestActionSerializer,
    OrganisationRequestCommsSerializer,
    OrganisationRequestDTSerializer,
    OrganisationRequestSerializer,
    OrganisationSerializer,
    OrgUserAcceptSerializer,
)
from disturbance.components.proposals.serializers import (
    DTProposalSerializer,
)
from disturbance.helpers import is_internal


class OrganisationViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = Organisation.objects.none()
    serializer_class = OrganisationSerializer
    allow_external = False  # NOTE: this is fine, but an alternative would be to use a direct get instead of going through get_queryset

    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request) or self.allow_external:
            return Organisation.objects.all()
        elif user.is_authenticated:
            return user.disturbance_organisations.all()
        return Organisation.objects.none()

    @action(
        detail=True,
        methods=[
            "GET",
        ],
    )
    def contacts(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.update_contacts(request)
        serializer = OrganisationContactSerializer(instance.contacts.exclude(user_status="pending"), many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "GET",
        ],
    )
    def contacts_linked(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = OrganisationContactSerializer(qs, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "GET",
        ],
    )
    def contacts_exclude(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.contacts.exclude(user_status="draft")
        serializer = OrganisationContactSerializer(qs, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "POST",
        ],
    )
    def validate_pins(self, request, *args, **kwargs):
        self.allow_external = True
        instance = self.get_object()
        serializer = OrganisationPinCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ret = instance.validate_pins(
            serializer.validated_data["pin1"],
            serializer.validated_data["pin2"],
            request,
        )

        if ret is None:
            # user has already been to this organisation - don't add again
            data = {"valid": ret}
            return Response({"valid": "User already exists"})

        data = {"valid": ret}
        if data["valid"]:
            # Notify each Admin member of request.
            instance.send_organisation_request_link_notification(request)
        return Response(data)

    @action(
        detail=True,
        methods=[
            "POST",
        ],
    )
    def accept_user(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = OrgUserAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_obj = EmailUser.objects.get(email=serializer.validated_data["email"].lower())
        instance.accept_user(user_obj, request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "POST",
        ],
    )
    def accept_declined_user(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = OrgUserAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_obj = EmailUser.objects.get(email=serializer.validated_data["email"].lower())
        instance.accept_declined_user(user_obj, request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "POST",
        ],
    )
    def decline_user(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = OrgUserAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_obj = EmailUser.objects.get(email=serializer.validated_data["email"].lower())
        instance.decline_user(user_obj, request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "POST",
        ],
    )
    def unlink_user(self, request, *args, **kwargs):
        self.allow_external = True
        instance = self.get_object()
        serializer = OrgUserAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_obj = EmailUser.objects.get(email=serializer.validated_data["email"].lower())
        instance.unlink_user(user_obj, request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "POST",
        ],
    )
    def make_admin_user(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = OrgUserAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_obj = EmailUser.objects.get(email=serializer.validated_data["email"].lower())
        instance.make_admin_user(user_obj, request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "POST",
        ],
    )
    def make_user(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = OrgUserAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_obj = EmailUser.objects.get(email=serializer.validated_data["email"].lower())
        instance.make_user(user_obj, request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "POST",
        ],
    )
    def make_consultant(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = OrgUserAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_obj = EmailUser.objects.get(email=serializer.validated_data["email"].lower())
        instance.make_consultant(user_obj, request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "POST",
        ],
    )
    def suspend_user(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = OrgUserAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_obj = EmailUser.objects.get(email=serializer.validated_data["email"].lower())
        instance.suspend_user(user_obj, request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "POST",
        ],
    )
    def reinstate_user(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = OrgUserAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_obj = EmailUser.objects.get(email=serializer.validated_data["email"].lower())
        instance.reinstate_user(user_obj, request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "POST",
        ],
    )
    def relink_user(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = OrgUserAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_obj = EmailUser.objects.get(email=serializer.validated_data["email"].lower())
        instance.relink_user(user_obj, request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "GET",
        ],
        permission_classes=[InternalOrganisationPermission],
    )
    def action_log(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.action_logs.all()
        serializer = OrganisationActionSerializer(qs, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "GET",
        ],
    )
    def proposals(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.proposals.all()
        serializer = DTProposalSerializer(qs, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "GET",
        ],
        permission_classes=[InternalOrganisationPermission],
    )
    def comms_log(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.comms_logs.all()
        serializer = OrganisationCommsSerializer(qs, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "POST",
        ],
        permission_classes=[InternalOrganisationPermission],
    )
    @renderer_classes((JSONRenderer,))
    def add_comms_log(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            request_data = request.data.copy()
            request_data["organisation"] = f"{instance.id}"
            request_data["staff"] = f"{request.user.id}"
            serializer = OrganisationLogEntrySerializer(data=request_data)
            serializer.is_valid(raise_exception=True)

            comms = serializer.save()

            # Save the files
            for f in request.FILES.getlist("files"):
                document = comms.documents.create()
                document.check_file(f)
                document.name = str(f)
                document._file = f
                document.save()

            return Response(serializer.data)

    @action(
        detail=False,
        methods=[
            "POST",
        ],
    )
    def existence(self, request, *args, **kwargs):
        serializer = OrganisationCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = Organisation.existence(serializer.validated_data["abn"])
        data.update([("user", request.user.id)])
        data.update([("abn", request.data["abn"])])
        serializer = OrganisationCheckExistSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class OrganisationRequestsViewSet(viewsets.ReadOnlyModelViewSet, mixins.RetrieveModelMixin):
    queryset = OrganisationRequest.objects.all()
    serializer_class = OrganisationRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request):
            qs = OrganisationRequest.objects.all().order_by("-lodgement_date")
            return qs
        elif user.is_authenticated:
            return user.organisationrequest_set.all()
        return OrganisationRequest.objects.none()

    @action(
        detail=False,
        methods=[
            "GET",
        ],
        permission_classes=[InternalOrganisationPermission],
    )
    def datatable_list(self, request, *args, **kwargs):
        template_group = get_template_group(request)
        qs = self.get_queryset().filter(template_group=template_group)
        serializer = OrganisationRequestDTSerializer(qs, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=[
            "GET",
        ],
        permission_classes=[InternalOrganisationPermission],
    )
    def user_list(self, request, *args, **kwargs):
        qs = self.get_queryset().filter(requester=request.user, status="with_assessor")
        serializer = OrganisationRequestDTSerializer(qs, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=[
            "GET",
        ],
    )
    def get_pending_requests(self, request, *args, **kwargs):
        qs = self.get_queryset().filter(requester=request.user, status="with_assessor")
        serializer = OrganisationRequestDTSerializer(qs, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=[
            "GET",
        ],
    )
    def get_amendment_requested_requests(self, request, *args, **kwargs):
        qs = self.get_queryset().filter(requester=request.user, status="amendment_requested")
        serializer = OrganisationRequestDTSerializer(qs, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "GET",
        ],
        permission_classes=[OrganisationRequestAssessorPermission],
    )
    def assign_request_user(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.assign_to(request.user, request)
        serializer = OrganisationRequestSerializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "GET",
        ],
        permission_classes=[OrganisationRequestAssessorPermission],
    )
    def unassign(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.unassign(request)
        serializer = OrganisationRequestSerializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "GET",
        ],
        permission_classes=[OrganisationRequestAssessorPermission],
    )
    def accept(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.accept(request)
        serializer = OrganisationRequestSerializer(instance)
        return Response(serializer.data)

    # TODO on-cleanup - is this used? remove if not
    @action(
        detail=True,
        methods=[
            "GET",
        ],
        permission_classes=[InternalOrganisationPermission],
    )
    def amendment_request(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.amendment_request(request)
        serializer = OrganisationRequestSerializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "GET",
        ],
        permission_classes=[OrganisationRequestAssessorPermission],
    )
    def decline(self, request, *args, **kwargs):
        instance = self.get_object()
        reason = ""
        instance.decline(reason, request)
        serializer = OrganisationRequestSerializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "POST",
        ],
        permission_classes=[OrganisationRequestAssessorPermission],
    )
    def assign_to(self, request, *args, **kwargs):
        instance = self.get_object()
        user_id = request.data.get("user_id", None)
        user = None
        if user_id is not None:
            try:
                user = EmailUser.objects.get(id=user_id)
            except EmailUser.DoesNotExist:
                raise serializers.ValidationError("A user with the id passed in does not exist")
        instance.assign_to(user, request)
        serializer = OrganisationRequestSerializer(instance)

        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "GET",
        ],
        permission_classes=[InternalOrganisationPermission],
    )
    def action_log(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.action_logs.all()
        serializer = OrganisationRequestActionSerializer(qs, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "GET",
        ],
        permission_classes=[InternalOrganisationPermission],
    )
    def comms_log(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.comms_logs.all()
        serializer = OrganisationRequestCommsSerializer(qs, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=[
            "POST",
        ],
        permission_classes=[InternalOrganisationPermission],
    )
    @renderer_classes((JSONRenderer,))
    def add_comms_log(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            request_data = request.data.copy()
            request_data["request"] = f"{instance.id}"
            request_data["staff"] = f"{request.user.id}"
            serializer = OrganisationRequestCommsSerializer(data=request_data)
            serializer.is_valid(raise_exception=True)

            comms = serializer.save()

            # Save the files
            for f in request.FILES.getlist("files"):
                document = comms.documents.create()
                document.check_file(f)
                document.name = str(f)
                document._file = f
                document.save()

            # End Save Documents

            return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data["requester"] = request.user
        if request.data["role"] == "consultant":
            # Check if consultant can be relinked to org.
            data = Organisation.existence(request.data["abn"])
            data.update([("user", request.user.id)])
            data.update([("abn", request.data["abn"])])
            existing_org = OrganisationCheckExistSerializer(data=data)
            existing_org.is_valid(raise_exception=True)
        with transaction.atomic():
            instance = serializer.save()
            # now set template_group
            template_group = get_template_group(request)
            instance.template_group = template_group
            instance.save()
            instance.log_user_action(
                OrganisationRequestUserAction.ACTION_LODGE_REQUEST.format(instance.id),
                request,
            )
            instance.send_organisation_request_email_notification(request, template_group)
        return Response(serializer.data)


class OrganisationAccessGroupMembers(views.APIView):
    permission_classes = [InternalOrganisationPermission]
    renderer_classes = [
        JSONRenderer,
    ]

    def get(self, request, format=None):
        members = []
        group = OrganisationAccessGroup.objects.first()
        if group:
            for m in group.all_members:
                members.append({"name": m.get_full_name(), "id": m.id})
        else:
            for m in EmailUser.objects.filter(is_superuser=True, is_staff=True, is_active=True):
                members.append({"name": m.get_full_name(), "id": m.id})
        return Response(members)


class ApiaryOrganisationAccessGroupMembers(views.APIView):
    permission_classes = [InternalOrganisationPermission]
    renderer_classes = [
        JSONRenderer,
    ]

    def get(self, request, format=None):
        members = []
        group = ApiaryOrganisationAccessGroup.objects.first()
        if group:
            for m in group.all_members:
                members.append({"name": m.get_full_name(), "id": m.id})
        else:
            for m in EmailUser.objects.filter(is_superuser=True, is_staff=True, is_active=True):
                members.append({"name": m.get_full_name(), "id": m.id})
        return Response(members)


class OrganisationContactViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    serializer_class = OrganisationContactSerializer
    queryset = OrganisationContact.objects.all()

    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request):
            return OrganisationContact.objects.all()
        elif user.is_authenticated:
            user_orgs = [org.id for org in user.disturbance_organisations.all()]
            return OrganisationContact.objects.filter(Q(organisation_id__in=user_orgs))
        return OrganisationContact.objects.none()

    def destroy(self, request, *args, **kwargs):
        """delete an Organisation contact"""
        num_admins = self.get_object().organisation.contacts.filter(is_admin=True).count()
        org_contact = self.get_object().organisation.contacts.get(id=kwargs["pk"])
        if num_admins == 1 and org_contact.is_admin:
            raise serializers.ValidationError("Cannot delete the last Organisation Admin")
        return super().destroy(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if "contact_form" in request.data.get("user_status"):
            serializer.save(user_status="contact_form")
        else:
            serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MyOrganisationsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Organisation.objects.all()
    serializer_class = MyOrganisationsSerializer

    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request):
            qs = Organisation.objects.all()
        elif user.is_authenticated:
            qs = user.disturbance_organisations.all()
        else:
            return Organisation.objects.none()

        search_term = self.request.query_params.get("search", "").strip()
        if search_term:
            qs = qs.filter(
                Q(property_cache__name__icontains=search_term) | Q(property_cache__abn__icontains=search_term)
            )

        return qs.order_by("property_cache__name", "id")


class GetOrganisationId(views.APIView):
    renderer_classes = [
        JSONRenderer,
    ]

    def get(self, request, format=None):

        org_id = request.GET.get("org_id", "")
        user = self.request.user
        if is_internal(self.request):
            organisation_qs = Organisation.objects.filter(organisation_id=org_id)
        elif user.is_authenticated:
            organisation_qs = user.disturbance_organisations.filter(organisation_id=org_id)

        if organisation_qs.exists():
            return Response({"id": organisation_qs.last().id})
        else:
            raise serializers.ValidationError("not authorised to access organisation")

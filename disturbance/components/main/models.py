import logging
import os
import uuid
from datetime import date, datetime

from dirtyfields import DirtyFieldsMixin
from django.apps import apps
from django.conf import settings
from django.contrib.gis.db.models import MultiPolygonField
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models import JSONField
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from six import python_2_unicode_compatible

from disturbance.components.main.utils import (
    check_file,
    overwrite_districts_polygons,
    overwrite_regions_polygons,
)

logger = logging.getLogger(__name__)
private_storage = FileSystemStorage(location=settings.BASE_DIR + "/private-media/", base_url="/private-media/")


class SanitiseMixin(models.Model):
    """
    Sanitise models fields
    """

    def save(self, **kwargs):
        from disturbance.components.main.utils import sanitise_fields

        # sanitise
        exclude = kwargs.pop("exclude_sanitise", [])  # fields that should not be subject to full tag removal
        error_on_change = kwargs.pop(
            "error_on_sanitise", []
        )  # fields that should not be modified through tag removal (and should throw and error if they are)
        self = sanitise_fields(self, exclude, error_on_change)
        super().save(**kwargs)

    class Meta:
        abstract = True


class RevisionedMixin(SanitiseMixin):
    """
    A model tracked by reversion through the save method.
    """

    def save(self, **kwargs):
        from reversion import revisions

        if kwargs.pop("no_revision", False):
            super().save(**kwargs)
        else:
            with revisions.create_revision():
                if "version_user" in kwargs:
                    revisions.set_user(kwargs.pop("version_user", None))
                if "version_comment" in kwargs:
                    revisions.set_comment(kwargs.pop("version_comment", ""))
                super().save(**kwargs)

    @property
    def created_date(self):
        from reversion.models import Version

        return Version.objects.get_for_object(self).last().revision.date_created

    @property
    def modified_date(self):
        from reversion.models import Version

        return Version.objects.get_for_object(self).first().revision.date_created

    class Meta:
        abstract = True


class SanitiseFileMixin(SanitiseMixin, DirtyFieldsMixin):
    """
    Sanitise file extensions and names
    """

    def auto_generate_file_name(self, extension):
        return f"{self._meta.model_name}_{uuid.uuid4()}_{int(datetime.now().timestamp() * 100000)}.{extension}"

    def save(self, **kwargs):
        from disturbance.components.main.utils import check_file

        path_to_file = kwargs.pop("path_to_file", None)
        file_content = kwargs.pop("file_content", None)
        storage = kwargs.pop("storage", None)
        file_field = kwargs.pop("file_field", "_file")

        if not hasattr(self, file_field):
            # if no file field is provided, get the first filefield on the model (this mixin is designed to handle one filefield per model, but can multiple can be handled with separate saves)
            for field in self._meta.get_fields():
                if isinstance(field, models.FileField):
                    file_field = field.attname
                    break

        if not path_to_file:
            try:
                # we specify an empty string here so we can substitute our own (NOTE: may be worth changing how this works to just return the path)
                if isinstance(self._meta.get_field(file_field).upload_to, str):
                    path_to_file = self._meta.get_field(file_field).upload_to
                else:
                    path_to_file = self._meta.get_field(file_field).upload_to(self, "")
            except Exception as e:
                print(e)
                path_to_file = None

        if not storage:
            storage = self._meta.get_field(file_field).storage

        if not file_content:
            try:
                file_content = getattr(self, file_field)
            except Exception as e:
                print(e)
                file_content = None

        file_content_exists = True
        if path_to_file and file_content and storage:
            try:
                _ = getattr(file_content, "size")
            except AttributeError:
                file_content_exists = False
            except FileNotFoundError:
                logger.warning(
                    "File not found for model=%s file=%s", self._meta.model_name, str(file_content)
                )
                file_content_exists = False
            except Exception as e:
                logger.exception(
                    "Error reading file size for model=%s file=%s: %s", self._meta.model_name, str(file_content), e
                )
                file_content_exists = False

        # if file content does not exist, it does not need to be sanitised
        if not file_content_exists:
            super().save(**kwargs)
            return

        if path_to_file and file_content and storage:
            # check file extension
            check_file(file_content, self._meta.model_name)

            # check file size
            if file_content.size > settings.FILE_SIZE_LIMIT_BYTES:
                raise ValidationError(f"File size too large: Max {settings.FILE_SIZE_LIMIT_BYTES / 1000000}MB")

            # auto-gen file name
            _, extension = os.path.splitext(str(file_content))
            generated_file_name = self.auto_generate_file_name(extension.replace(".", ""))
            read = file_content.read()
            if bool(read):
                setattr(
                    self,
                    file_field,
                    storage.save(
                        f"{path_to_file}/{generated_file_name}",
                        ContentFile(read),
                    ),
                )
            else:
                logger.warning(
                    "Empty file upload rejected: model=%s file=%s",
                    self._meta.model_name,
                    str(file_content),
                )
                raise ValidationError("The uploaded file is empty. Please select a valid file.")
        elif file_field in self.get_dirty_fields() and self.get_dirty_fields()[file_field]:
            raise ValidationError("Cannot change file")

        # proceed with general sanitisation and save
        super().save(**kwargs)

    class Meta:
        abstract = True


class FileExtensionWhitelist(models.Model):
    name = models.CharField(
        max_length=16,
        help_text="The file extension without the dot, e.g. jpg, pdf, docx, etc",
    )
    model = models.CharField(max_length=255, default="all")

    class Meta:
        app_label = "disturbance"
        unique_together = ("name", "model")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta.get_field("model").choices = (
            (
                "all",
                "all",
            ),
        ) + tuple(
            map(
                lambda m: (m, m),
                filter(
                    lambda m: Document in apps.get_app_config("disturbance").models[m].__bases__,
                    apps.get_app_config("disturbance").models,
                ),
            )
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete(settings.CACHE_KEY_FILE_EXTENSION_WHITELIST)


class MapLayer(SanitiseMixin):
    display_name = models.CharField(max_length=100, blank=True, null=True)
    layer_name = models.CharField(max_length=200, blank=True, null=True)
    option_for_internal = models.BooleanField(default=True)
    option_for_external = models.BooleanField(default=True)
    display_all_columns = models.BooleanField(default=False)
    cache_expiry = models.IntegerField(default=300)

    class Meta:
        app_label = "disturbance"
        verbose_name = "apiary map layer"

    def __str__(self):
        return f"{self.display_name}, {self.layer_name}"

    @property
    def column_names(self):
        column_names = []
        for column in self.columns.all():
            column_names.append(column.name)
        return ",".join(column_names)

    def save(self, *args, **kwargs):
        cache.delete("utils_cache.get_proxy_cache()")
        self.full_clean()
        super().save(*args, **kwargs)


class MapColumn(SanitiseMixin):
    map_layer = models.ForeignKey(
        MapLayer,
        null=True,
        blank=True,
        related_name="columns",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=100, blank=True, null=True)
    option_for_internal = models.BooleanField(default=True)
    option_for_external = models.BooleanField(default=True)

    class Meta:
        app_label = "disturbance"
        verbose_name = "apiary map column"

    def __str__(self):
        return f"{self.map_layer}, {self.name}"


@python_2_unicode_compatible
class Region(SanitiseMixin):
    name = models.CharField(max_length=200, unique=True)
    forest_region = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        app_label = "disturbance"

    def __str__(self):
        return self.name


class ArchivedDistrictManager(models.Manager):
    def get_queryset(self):
        # return super().get_queryset().all()
        return super().get_queryset().exclude(archive_date__lte=date.today())


@python_2_unicode_compatible
class District(SanitiseMixin):
    region = models.ForeignKey(Region, related_name="districts", on_delete=models.CASCADE)
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=3)
    archive_date = models.DateField(null=True, blank=True)

    objects = ArchivedDistrictManager()

    class Meta:
        ordering = ["name"]
        app_label = "disturbance"

    def __str__(self):
        return self.name


class DistrictDbca(SanitiseMixin):
    wkb_geometry = MultiPolygonField(srid=4326, blank=True, null=True)
    district_name = models.CharField(max_length=200, blank=True, null=True)
    office = models.CharField(max_length=200, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = [
            "object_id",
        ]
        app_label = "disturbance"
        verbose_name_plural = "Apiary DBCA Districts"


class RegionDbca(SanitiseMixin):
    wkb_geometry = MultiPolygonField(srid=4326, blank=True, null=True)
    region_name = models.CharField(max_length=200, blank=True, null=True)
    office = models.CharField(max_length=200, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = [
            "object_id",
        ]
        app_label = "disturbance"
        verbose_name_plural = "Apiary DBCA Regions"


class CategoryDbca(SanitiseMixin):
    """
    This model is used for defining the categories
    """

    wkb_geometry = MultiPolygonField(srid=4326, blank=True, null=True)
    category_name = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        app_label = "disturbance"


class WaCoast(SanitiseMixin):
    """
    This model is used for validating if the apiary site is in the valid area
    """

    wkb_geometry = MultiPolygonField(srid=4326, blank=True, null=True)
    type = models.CharField(max_length=30, blank=True, null=True)
    source = models.CharField(max_length=50, blank=True, null=True)
    smoothed = models.BooleanField(default=False)

    class Meta:
        app_label = "disturbance"


@python_2_unicode_compatible
class ApplicationType(models.Model):
    DISTURBANCE = "Disturbance"
    DISTURBANCE_UAT = "Disturbance Training"
    DISTURBANCE_DEMO = "Disturbance Demo"
    POWERLINE_MAINTENANCE = "Powerline Maintenance"
    APIARY = "Apiary"
    TEMPORARY_USE = "Temporary Use"
    SITE_TRANSFER = "Site Transfer"
    FIRE = "Prescribed Burning"

    APPLICATION_TYPES = (
        (DISTURBANCE, "Disturbance"),
        (DISTURBANCE_UAT, "Disturbance Training"),
        (DISTURBANCE_DEMO, "Disturbance Demo"),
        (POWERLINE_MAINTENANCE, "Powerline Maintenance"),
        (APIARY, "Apiary"),
        (TEMPORARY_USE, "Temporary Use"),
        (SITE_TRANSFER, "Site Transfer"),
        (FIRE, "Prescribed Burning"),
    )

    APIARY_APPLICATION_TYPES = (
        APIARY,
        TEMPORARY_USE,
        SITE_TRANSFER,
    )

    DOMAIN_USED_CHOICES = (
        ("das", "DAS"),
        ("apiary", "Apiary"),
    )

    name = models.CharField(
        verbose_name="Application Type name",
        max_length=64,
        choices=APPLICATION_TYPES,
    )
    order = models.PositiveSmallIntegerField(default=0)
    visible = models.BooleanField(default=True)
    application_fee = models.DecimalField(max_digits=6, decimal_places=2)
    oracle_code_application = models.CharField(max_length=50)
    is_gst_exempt = models.BooleanField(default=True)
    domain_used = models.CharField(max_length=40, choices=DOMAIN_USED_CHOICES, default=DOMAIN_USED_CHOICES[0][0])
    searchable = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "name"]
        app_label = "disturbance"

    def __str__(self):
        return self.name


# TODO on-cleanup - work out if this is needed, remove if not
@python_2_unicode_compatible
class ActivityMatrix(models.Model):
    name = models.CharField(
        verbose_name="Activity matrix name",
        max_length=24,
        choices=[("Disturbance", "Disturbance")],
        default="Disturbance",
    )
    description = models.CharField(max_length=256, blank=True, null=True)
    schema = JSONField()
    replaced_by = models.ForeignKey("self", on_delete=models.PROTECT, blank=True, null=True)
    version = models.SmallIntegerField(default=1, blank=False, null=False)
    ordered = models.BooleanField("Activities Ordered Alphabetically", default=False)

    class Meta:
        app_label = "disturbance"
        unique_together = ("name", "version")
        verbose_name_plural = "Approval matrix"

    def __str__(self):
        return f"{self.name} - v{self.version}"


@python_2_unicode_compatible
class Tenure(SanitiseMixin):
    name = models.CharField(max_length=255, unique=True)
    order = models.PositiveSmallIntegerField(default=0)
    application_type = models.ForeignKey(ApplicationType, related_name="tenure_app_types", on_delete=models.CASCADE)

    class Meta:
        ordering = ["order", "name"]
        app_label = "disturbance"

    def __str__(self):
        return f"{self.name}: {self.application_type}"


@python_2_unicode_compatible
class UserAction(SanitiseMixin):
    who = models.ForeignKey(EmailUser, null=False, blank=False, on_delete=models.CASCADE)
    when = models.DateTimeField(null=False, blank=False, auto_now_add=True)
    what = models.TextField(blank=False)

    def __str__(self):
        return f"{self.what} ({self.who} at {self.when})"

    class Meta:
        abstract = True
        app_label = "disturbance"


class CommunicationsLogEntry(SanitiseMixin):
    TYPE_CHOICES = [
        ("email", "Email"),
        ("phone", "Phone Call"),
        ("mail", "Mail"),
        ("person", "In Person"),
        ("referral_complete", "Referral Completed"),
    ]
    DEFAULT_TYPE = TYPE_CHOICES[0][0]

    to = models.TextField(blank=True, verbose_name="To")
    fromm = models.CharField(max_length=200, blank=True, verbose_name="From")
    cc = models.TextField(blank=True, verbose_name="cc")

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=DEFAULT_TYPE)
    reference = models.CharField(max_length=100, blank=True)
    subject = models.CharField(max_length=200, blank=True, verbose_name="Subject / Description")
    text = models.TextField(blank=True)

    customer = models.ForeignKey(EmailUser, null=True, related_name="+", on_delete=models.CASCADE)
    staff = models.ForeignKey(EmailUser, null=True, related_name="+", on_delete=models.CASCADE)

    created = models.DateTimeField(auto_now_add=True, null=False, blank=False)

    class Meta:
        app_label = "disturbance"


@python_2_unicode_compatible
class LedgerDocument(SanitiseFileMixin):
    name = models.CharField(max_length=255, blank=True, verbose_name="name", help_text="")
    description = models.TextField(blank=True, verbose_name="description", help_text="")
    uploaded_date = models.DateTimeField(auto_now_add=True)

    @property
    def path(self):
        # return self.file.path
        return self._file.path

    @property
    def filename(self):
        return os.path.basename(self.path)

    def __str__(self):
        return self.name or self.filename

    def check_file(self, file):
        return check_file(file, self._meta.model_name)

    class Meta:
        app_label = "disturbance"


@python_2_unicode_compatible
class Document(SanitiseFileMixin):
    name = models.CharField(max_length=255, blank=True, verbose_name="name", help_text="")
    description = models.TextField(blank=True, verbose_name="description", help_text="")
    uploaded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "disturbance"
        abstract = True

    @property
    def path(self):
        # return self.file.path
        return self._file.path

    @property
    def filename(self):
        return os.path.basename(self.path)

    def __str__(self):
        return self.name or self.filename

    def check_file(self, file):
        return check_file(file, self._meta.model_name)

    class Meta:
        app_label = "disturbance"
        abstract = True


@python_2_unicode_compatible
class SystemMaintenance(SanitiseMixin):
    name = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def duration(self):
        """Duration of system maintenance (in mins)"""
        return (
            int((self.end_date - self.start_date).total_seconds() / 60.0) if self.end_date and self.start_date else ""
        )
        # return (datetime.now(tz=tz) - self.start_date).total_seconds()/60.

    duration.short_description = "Duration (mins)"

    class Meta:
        app_label = "disturbance"
        verbose_name_plural = "System maintenance"

    def __str__(self):
        return (
            f"System Maintenance: {self.name} ({self.description}) - starting {self.start_date}, ending {self.end_date}"
        )


@python_2_unicode_compatible
class ApiaryGlobalSettings(models.Model):
    KEY_ORACLE_CODE_APIARY_SITE_ANNUAL_RENTAL_FEE = "oracle_code_apiary_site_annural_rental_fee"  # ApplicationType object has an attribute 'oracle_code_application' to store oracle account code
    # However for the annual rental fee, there are not proposals, which means no ApplicationType objects related.
    # Therefore we store oracle account code for the annual site fee here.
    KEY_APIARY_SITES_LIST_TOKEN = "apiary_sites_list_token"
    KEY_APIARY_LICENCE_TEMPLATE_FILE = "apiary_licence_template_file"
    KEY_PRINT_DEED_POLL_URL = "print_deed_poll_url"
    KEY_DBCA_DISTRICTS_FILE = "dbca_districts_file"
    KEY_DBCA_REGIONS_FILE = "dbca_regions_file"

    keys = (
        (
            KEY_ORACLE_CODE_APIARY_SITE_ANNUAL_RENTAL_FEE,
            "Oracle code for the apiary site annual site fee",
        ),
        (KEY_APIARY_SITES_LIST_TOKEN, "Token to import the apiary sites list"),
        (KEY_APIARY_LICENCE_TEMPLATE_FILE, "Apiary licence template file"),
        (KEY_PRINT_DEED_POLL_URL, "URL of the deed poll"),
        (KEY_DBCA_DISTRICTS_FILE, "DBCA districts geojson file"),
        (KEY_DBCA_REGIONS_FILE, "DBCA regions geojson file"),
    )

    default_values = (
        (KEY_ORACLE_CODE_APIARY_SITE_ANNUAL_RENTAL_FEE, "T1 EXEMPT"),
        (KEY_APIARY_SITES_LIST_TOKEN, "abc123"),
        (KEY_APIARY_LICENCE_TEMPLATE_FILE, ""),
        (KEY_DBCA_DISTRICTS_FILE, ""),
        (KEY_DBCA_REGIONS_FILE, ""),
        (
            KEY_PRINT_DEED_POLL_URL,
            "https://parks.dpaw.wa.gov.au/sites/default/files/downloads/know/DBCA%20apiary%20deed%20poll.pdf",
        ),
    )
    key = models.CharField(max_length=255, choices=keys, blank=False, null=False, unique=True)
    value = models.CharField(max_length=255)
    _file = models.FileField(max_length=255, upload_to="apiary_licence_template", null=True, blank=True)

    class Meta:
        app_label = "disturbance"
        verbose_name_plural = "Apiary Global Settings"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)

        if self._file:
            # When regions/districts file has been updated, update polygons for it.
            if self.key == ApiaryGlobalSettings.KEY_DBCA_REGIONS_FILE:
                overwrite_regions_polygons(self._file.path)
            elif self.key == ApiaryGlobalSettings.KEY_DBCA_DISTRICTS_FILE:
                overwrite_districts_polygons(self._file.path)

    def __str__(self):
        return self.key


@python_2_unicode_compatible
class GlobalSettings(models.Model):
    KEY_ASSESSMENT_REMINDER_DAYS = "assessment_reminder_days"

    keys = ((KEY_ASSESSMENT_REMINDER_DAYS, "Assessment reminder days"),)
    default_values = ()
    key = models.CharField(max_length=255, choices=keys, blank=False, null=False, unique=True)
    value = models.CharField(max_length=255)

    class Meta:
        app_label = "disturbance"
        verbose_name_plural = "Global Settings"

    def __str__(self):
        return self.key


class TemporaryDocumentCollection(models.Model):
    class Meta:
        app_label = "disturbance"


# temp document obj for generic file upload component
class TemporaryDocument(Document):
    temp_document_collection = models.ForeignKey(
        TemporaryDocumentCollection, related_name="documents", on_delete=models.CASCADE
    )
    _file = models.FileField(max_length=255)

    class Meta:
        app_label = "disturbance"


class JobQueue(models.Model):
    STATUS = (
        (0, "Pending"),
        (1, "Running"),
        (2, "Completed"),
        (3, "Failed"),
    )

    job_cmd = models.CharField(max_length=1000, null=True, blank=True)
    system_id = models.CharField(max_length=4, null=True, blank=True)
    status = models.SmallIntegerField(choices=STATUS, default=0)
    parameters_json = models.JSONField(null=True, blank=True)
    processed_dt = models.DateTimeField(default=None, null=True, blank=True)
    user = models.IntegerField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "disturbance"

    def __str__(self):
        return self.job_cmd


import reversion

reversion.register(ApiaryGlobalSettings)

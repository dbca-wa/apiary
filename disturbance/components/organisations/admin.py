from django.contrib import admin
from ledger_api_client.ledger_models import EmailUserRO as EmailUser

from disturbance.components.organisations import models

# Register your models here.

# @admin.register(models.Organisation)
# class OrganisationAdmin(admin.ModelAdmin):
#     list_display = ['organisation','pin_one', 'pin_two']
#     readonly_fields = ['pin_one', 'pin_two']


class OrganisationContactInline(admin.TabularInline):
    model = models.OrganisationContact
    extra = 0


@admin.register(models.Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "abn",
        "organisation_id",
        "admin_pin_one",
        "admin_pin_two",
        "user_pin_one",
        "user_pin_two",
    ]

    search_fields = ["id", "property_cache__name", "property_cache__abn"]

    inlines = [
        OrganisationContactInline,
    ]


@admin.register(models.OrganisationRequest)
class OrganisationRequestAdmin(admin.ModelAdmin):
    raw_id_fields = ("requester", "assigned_officer")
    list_display = ["id", "name", "lodgement_date"]
    search_fields = ["id", "name", "lodgement_date"]


# class OrganisationAccessGroupMembershipInline(admin.TabularInline):
#    model = models.OrganisationAccessGroupMember
#    extra = 1
#    raw_id_fields = ('emailuser',)

# @admin.register(models.OrganisationAccessGroup)
# class OrganisationAccessGroupAdmin(admin.ModelAdmin):
#    # filter_horizontal = ('members',)
#    exclude = ('site',)
#    actions = None
#    inlines = [OrganisationAccessGroupMembershipInline,]
#
#    def formfield_for_manytomany(self, db_field, request, **kwargs):
#        if db_field.name == "members":
#            #kwargs["queryset"] = EmailUser.objects.filter(email__icontains='@dbca.wa.gov.au')
#            kwargs["queryset"] = EmailUser.objects.filter(is_staff=True)
#        return super(OrganisationAccessGroupAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)
#
#    def has_add_permission(self, request):
#        return True if models.OrganisationAccessGroup.objects.count() == 0 else False
#
#    def has_delete_permission(self, request, obj=None):
#        return False


class ApiaryOrganisationAccessGroupMembershipInline(admin.TabularInline):
    model = models.ApiaryOrganisationAccessGroupMember
    extra = 1
    raw_id_fields = ("emailuser",)


@admin.register(models.ApiaryOrganisationAccessGroup)
class ApiaryOrganisationAccessGroupAdmin(admin.ModelAdmin):
    # filter_horizontal = ('members',)
    exclude = ("site",)
    actions = None
    inlines = [
        ApiaryOrganisationAccessGroupMembershipInline,
    ]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "members":
            # kwargs["queryset"] = EmailUser.objects.filter(email__icontains='@dbca.wa.gov.au')
            kwargs["queryset"] = EmailUser.objects.filter(is_staff=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return True if models.ApiaryOrganisationAccessGroup.objects.count() == 0 else False

    def has_delete_permission(self, request, obj=None):
        return False

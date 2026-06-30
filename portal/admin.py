"""Admin configuration for DHO/CEO oversight (spec sections 2 and 6)."""

from django.contrib import admin
from import_export.admin import ExportMixin

from .models import Applicant, Facility, Preference, Taluka, UGQualification
from .resources import ApplicantResource


@admin.register(UGQualification)
class UGQualificationAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Taluka)
class TalukaAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "taluka", "sanctioned_vacancies"]
    list_filter = ["taluka", "type"]
    search_fields = ["name"]
    autocomplete_fields = ["taluka"]


class PreferenceInline(admin.TabularInline):
    model = Preference
    extra = 0
    max_num = 3
    autocomplete_fields = ["facility"]


@admin.register(Applicant)
class ApplicantAdmin(ExportMixin, admin.ModelAdmin):
    resource_classes = [ApplicantResource]
    inlines = [PreferenceInline]
    list_display = [
        "full_name",
        "phone",
        "email",
        "ug_qualification",
        "priority_1_facility",
        "created_at",
    ]
    list_filter = ["ug_qualification", "created_at"]
    search_fields = ["first_name", "last_name", "father_name", "phone", "email"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        # Pull related rows used in list_display to avoid per-row queries.
        return (
            super()
            .get_queryset(request)
            .select_related("ug_qualification")
            .prefetch_related("preferences__facility__taluka")
        )

    @admin.display(description="Priority 1 facility")
    def priority_1_facility(self, obj):
        pref = next(
            (p for p in obj.preferences.all() if p.priority == 1), None
        )
        return pref.facility.name if pref else "—"

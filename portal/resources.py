"""Excel/CSV export definition for applicants (spec section 6).

Flattens each applicant's three prioritised facility choices into columns so the
DHO/CEO get one row per applicant in the downloaded spreadsheet.
"""

from import_export import fields, resources

from .models import Applicant


class ApplicantResource(resources.ModelResource):
    reference = fields.Field(attribute="reference_number", column_name="Reference")
    ug_qualification = fields.Field(
        attribute="ug_qualification__name", column_name="UG Qualification"
    )
    priority_1 = fields.Field(column_name="Priority 1")
    priority_2 = fields.Field(column_name="Priority 2")
    priority_3 = fields.Field(column_name="Priority 3")

    class Meta:
        model = Applicant
        fields = (
            "reference",
            "first_name",
            "father_name",
            "last_name",
            "dob",
            "address",
            "email",
            "phone",
            "ug_qualification",
            "ug_score",
            "score_type",
            "higher_qualification",
            "priority_1",
            "priority_2",
            "priority_3",
            "created_at",
        )
        export_order = fields

    def _facility_for(self, applicant, priority):
        pref = next(
            (p for p in applicant.preferences.all() if p.priority == priority),
            None,
        )
        if pref is None:
            return ""
        return f"{pref.facility.name} ({pref.facility.type}) — {pref.facility.taluka.name}"

    def dehydrate_priority_1(self, applicant):
        return self._facility_for(applicant, 1)

    def dehydrate_priority_2(self, applicant):
        return self._facility_for(applicant, 2)

    def dehydrate_priority_3(self, applicant):
        return self._facility_for(applicant, 3)

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Applicant, Facility, Preference, Taluka


class ApplicantForm(forms.ModelForm):
    # Priority dropdowns — unpopulated at load time, filled via AJAX on taluka change.
    taluka = forms.ModelChoiceField(
        queryset=Taluka.objects.all(),
        empty_label="— Select taluka —",
        label="Taluka",
    )
    priority_1 = forms.ModelChoiceField(
        queryset=Facility.objects.none(),
        empty_label="— Select facility —",
        label="Priority 1",
    )
    priority_2 = forms.ModelChoiceField(
        queryset=Facility.objects.none(),
        empty_label="— Select facility —",
        label="Priority 2",
    )
    priority_3 = forms.ModelChoiceField(
        queryset=Facility.objects.none(),
        empty_label="— Select facility —",
        label="Priority 3",
    )

    class Meta:
        model = Applicant
        fields = [
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
        ]
        widgets = {
            "dob": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If the form is submitted, populate priority dropdowns with facilities
        # from the submitted taluka so validation can resolve the FK values.
        if "taluka" in self.data:
            try:
                taluka_id = int(self.data["taluka"])
                qs = Facility.objects.filter(taluka_id=taluka_id).select_related("taluka")
                self.fields["priority_1"].queryset = qs
                self.fields["priority_2"].queryset = qs
                self.fields["priority_3"].queryset = qs
            except (ValueError, TypeError):
                pass

        self.fields["ug_qualification"].empty_label = "— Select qualification —"
        self.fields["higher_qualification"].required = False

    def clean_email(self):
        email = self.cleaned_data["email"]
        if Applicant.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "An application with this email address already exists."
            )
        return email

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if Applicant.objects.filter(phone=phone).exists():
            raise ValidationError(
                "An application with this phone number already exists."
            )
        return phone

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("priority_1")
        p2 = cleaned.get("priority_2")
        p3 = cleaned.get("priority_3")

        facilities = [f for f in (p1, p2, p3) if f is not None]
        if len(facilities) < 3:
            # Individual field errors already raised; skip cross-field check.
            return cleaned

        if len(set(f.pk for f in facilities)) < 3:
            raise ValidationError(
                "Each priority must be a different facility. "
                "You cannot select the same facility twice."
            )
        return cleaned

    @transaction.atomic
    def save(self, commit=True):
        applicant = super().save(commit=False)
        if commit:
            applicant.save()
            for priority, facility in enumerate(
                [
                    self.cleaned_data["priority_1"],
                    self.cleaned_data["priority_2"],
                    self.cleaned_data["priority_3"],
                ],
                start=1,
            ):
                Preference.objects.create(
                    applicant=applicant,
                    priority=priority,
                    facility=facility,
                )
        return applicant

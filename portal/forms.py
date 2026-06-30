from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Applicant, Facility, Preference, Taluka


class ApplicantForm(forms.ModelForm):
    # Each priority has its own taluka selector that independently filters its facility list.
    taluka_1 = forms.ModelChoiceField(
        queryset=Taluka.objects.all(), empty_label="— Select taluka —", label="Taluka"
    )
    priority_1 = forms.ModelChoiceField(
        queryset=Facility.objects.none(), empty_label="— Select facility —", label="Facility"
    )
    taluka_2 = forms.ModelChoiceField(
        queryset=Taluka.objects.all(), empty_label="— Select taluka —", label="Taluka"
    )
    priority_2 = forms.ModelChoiceField(
        queryset=Facility.objects.none(), empty_label="— Select facility —", label="Facility"
    )
    taluka_3 = forms.ModelChoiceField(
        queryset=Taluka.objects.all(), empty_label="— Select taluka —", label="Taluka"
    )
    priority_3 = forms.ModelChoiceField(
        queryset=Facility.objects.none(), empty_label="— Select facility —", label="Facility"
    )

    class Meta:
        model = Applicant
        fields = [
            "first_name", "father_name", "last_name", "dob", "address",
            "email", "phone", "ug_qualification", "ug_score", "score_type",
            "higher_qualification",
        ]
        widgets = {
            "dob": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # On POST (including validation-error re-render), populate each priority's
        # facility queryset from its own submitted taluka so FK validation works.
        for i in (1, 2, 3):
            taluka_key = f"taluka_{i}"
            priority_key = f"priority_{i}"
            if taluka_key in self.data:
                try:
                    taluka_id = int(self.data[taluka_key])
                    self.fields[priority_key].queryset = (
                        Facility.objects.filter(taluka_id=taluka_id)
                        .select_related("taluka")
                    )
                except (ValueError, TypeError):
                    pass

        self.fields["ug_qualification"].empty_label = "— Select qualification —"
        self.fields["higher_qualification"].required = False

    def clean_email(self):
        email = self.cleaned_data["email"]
        if Applicant.objects.filter(email__iexact=email).exists():
            raise ValidationError("An application with this email address already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if Applicant.objects.filter(phone=phone).exists():
            raise ValidationError("An application with this phone number already exists.")
        return phone

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("priority_1")
        p2 = cleaned.get("priority_2")
        p3 = cleaned.get("priority_3")

        facilities = [f for f in (p1, p2, p3) if f is not None]
        if len(facilities) < 3:
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
                [self.cleaned_data["priority_1"],
                 self.cleaned_data["priority_2"],
                 self.cleaned_data["priority_3"]],
                start=1,
            ):
                Preference.objects.create(
                    applicant=applicant, priority=priority, facility=facility
                )
        return applicant

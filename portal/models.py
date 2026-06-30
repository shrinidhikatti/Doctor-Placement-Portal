"""Data model for the Doctor Placement Portal (spec section 5)."""

from django.core.validators import RegexValidator
from django.db import models


class UGQualification(models.Model):
    """UG degree options shown in the application form (e.g. MBBS, BDS, BAMS)."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "UG qualification"

    def __str__(self):
        return self.name


class Taluka(models.Model):
    """A taluka of Belagavi district."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Facility(models.Model):
    """A PHC or CHC belonging to a taluka, with its sanctioned vacancy count."""

    class FacilityType(models.TextChoices):
        PHC = "PHC", "PHC"
        CHC = "CHC", "CHC"

    taluka = models.ForeignKey(
        Taluka, on_delete=models.PROTECT, related_name="facilities"
    )
    name = models.CharField(max_length=150)
    type = models.CharField(max_length=3, choices=FacilityType.choices)
    sanctioned_vacancies = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["taluka__name", "name"]
        verbose_name_plural = "Facilities"
        constraints = [
            models.UniqueConstraint(
                fields=["taluka", "name", "type"],
                name="unique_facility_per_taluka",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.type}) — {self.taluka.name}"


class Applicant(models.Model):
    """A graduate doctor's submitted application (spec section 3)."""

    class ScoreType(models.TextChoices):
        CGPA = "CGPA", "CGPA"
        PERCENTAGE = "PERCENTAGE", "Percentage"

    phone_validator = RegexValidator(
        regex=r"^\d{10}$",
        message="Phone number must be exactly 10 digits.",
    )

    # Personal details
    first_name = models.CharField(max_length=80)
    father_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    dob = models.DateField("date of birth")
    address = models.TextField("correspondence address")
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=10, unique=True, validators=[phone_validator]
    )

    # Education
    ug_qualification = models.ForeignKey(
        UGQualification, on_delete=models.PROTECT, related_name="applicants"
    )
    ug_score = models.DecimalField(max_digits=5, decimal_places=2)
    score_type = models.CharField(max_length=10, choices=ScoreType.choices)
    higher_qualification = models.CharField(max_length=150, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def reference_number(self):
        """Human-friendly reference shown on the confirmation screen."""
        return f"BLG-{self.pk:05d}"


class Preference(models.Model):
    """One prioritised facility choice (priority 1, 2, or 3) for an applicant."""

    class Priority(models.IntegerChoices):
        FIRST = 1, "Priority 1"
        SECOND = 2, "Priority 2"
        THIRD = 3, "Priority 3"

    applicant = models.ForeignKey(
        Applicant, on_delete=models.CASCADE, related_name="preferences"
    )
    priority = models.PositiveSmallIntegerField(choices=Priority.choices)
    facility = models.ForeignKey(
        Facility, on_delete=models.PROTECT, related_name="preferences"
    )

    class Meta:
        ordering = ["applicant", "priority"]
        constraints = [
            # An applicant lists each priority slot once...
            models.UniqueConstraint(
                fields=["applicant", "priority"],
                name="unique_applicant_priority",
            ),
            # ...and cannot pick the same facility in two slots.
            models.UniqueConstraint(
                fields=["applicant", "facility"],
                name="unique_applicant_facility",
            ),
        ]

    def __str__(self):
        return f"{self.applicant} → P{self.priority}: {self.facility.name}"

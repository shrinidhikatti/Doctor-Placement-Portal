"""
End-to-end tests for Phase 5 hardening.

Coverage:
- Public application form: valid submit, duplicate email, duplicate phone,
  same facility in two priorities, missing required fields.
- Facilities AJAX endpoint: no param, valid taluka, invalid taluka.
- Dashboard: anonymous redirect, staff access.
- Admin: anonymous redirect.
- DB integrity: unique constraints on Applicant and Preference.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Applicant, Facility, Preference, Taluka, UGQualification

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_master_data():
    qual = UGQualification.objects.create(name="MBBS")
    taluka = Taluka.objects.create(name="Belagavi")
    f1 = Facility.objects.create(taluka=taluka, name="PHC A", type="PHC", sanctioned_vacancies=2)
    f2 = Facility.objects.create(taluka=taluka, name="PHC B", type="PHC", sanctioned_vacancies=1)
    f3 = Facility.objects.create(taluka=taluka, name="CHC C", type="CHC", sanctioned_vacancies=3)
    return qual, taluka, f1, f2, f3


def valid_post(taluka, qual, f1, f2, f3, **overrides):
    data = {
        "first_name": "Test",
        "father_name": "Father",
        "last_name": "Doctor",
        "dob": "1995-06-15",
        "address": "123 Main St, Belagavi",
        "email": "test@example.com",
        "phone": "9876543210",
        "ug_qualification": qual.pk,
        "ug_score": "75.50",
        "score_type": "PERCENTAGE",
        "higher_qualification": "",
        "taluka_1": taluka.pk,
        "priority_1": f1.pk,
        "taluka_2": taluka.pk,
        "priority_2": f2.pk,
        "taluka_3": taluka.pk,
        "priority_3": f3.pk,
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# Application form tests
# ---------------------------------------------------------------------------

class ApplyViewTests(TestCase):

    def setUp(self):
        self.qual, self.taluka, self.f1, self.f2, self.f3 = make_master_data()
        self.url = reverse("portal:apply")

    def test_get_returns_form(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Application for Doctor Posting")

    def test_valid_submit_creates_applicant_and_preferences(self):
        data = valid_post(self.taluka, self.qual, self.f1, self.f2, self.f3)
        r = self.client.post(self.url, data)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "successfully submitted")
        self.assertEqual(Applicant.objects.count(), 1)
        self.assertEqual(Preference.objects.count(), 3)

    def test_confirmation_shows_reference_number(self):
        data = valid_post(self.taluka, self.qual, self.f1, self.f2, self.f3)
        r = self.client.post(self.url, data)
        self.assertContains(r, "BLG-")

    def test_preferences_saved_in_correct_order(self):
        data = valid_post(self.taluka, self.qual, self.f1, self.f2, self.f3)
        self.client.post(self.url, data)
        applicant = Applicant.objects.get()
        prefs = {p.priority: p.facility for p in applicant.preferences.all()}
        self.assertEqual(prefs[1], self.f1)
        self.assertEqual(prefs[2], self.f2)
        self.assertEqual(prefs[3], self.f3)

    def test_duplicate_email_rejected(self):
        data = valid_post(self.taluka, self.qual, self.f1, self.f2, self.f3)
        self.client.post(self.url, data)
        # Second submission with same email, different phone
        data2 = valid_post(self.taluka, self.qual, self.f1, self.f2, self.f3,
                           email="test@example.com", phone="9000000001")
        r = self.client.post(self.url, data2)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "already exists")
        self.assertEqual(Applicant.objects.count(), 1)

    def test_duplicate_phone_rejected(self):
        data = valid_post(self.taluka, self.qual, self.f1, self.f2, self.f3)
        self.client.post(self.url, data)
        data2 = valid_post(self.taluka, self.qual, self.f1, self.f2, self.f3,
                           email="other@example.com", phone="9876543210")
        r = self.client.post(self.url, data2)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "already exists")
        self.assertEqual(Applicant.objects.count(), 1)

    def test_same_facility_in_two_priorities_rejected(self):
        # Priority 1 and Priority 2 are the same facility
        data = valid_post(self.taluka, self.qual, self.f1, self.f2, self.f3,
                          priority_2=self.f1.pk)
        r = self.client.post(self.url, data)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "same facility")
        self.assertEqual(Applicant.objects.count(), 0)

    def test_missing_required_field_rejected(self):
        data = valid_post(self.taluka, self.qual, self.f1, self.f2, self.f3)
        del data["first_name"]
        r = self.client.post(self.url, data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Applicant.objects.count(), 0)

    def test_invalid_phone_rejected(self):
        data = valid_post(self.taluka, self.qual, self.f1, self.f2, self.f3,
                          phone="123")  # only 3 digits
        r = self.client.post(self.url, data)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "10 digits")
        self.assertEqual(Applicant.objects.count(), 0)

    def test_invalid_email_rejected(self):
        data = valid_post(self.taluka, self.qual, self.f1, self.f2, self.f3,
                          email="not-an-email")
        r = self.client.post(self.url, data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Applicant.objects.count(), 0)

    def test_no_partial_save_on_invalid_preferences(self):
        """If preference validation fails, no Applicant row should be created."""
        data = valid_post(self.taluka, self.qual, self.f1, self.f2, self.f3,
                          priority_1=self.f1.pk, priority_2=self.f1.pk, priority_3=self.f1.pk)
        self.client.post(self.url, data)
        self.assertEqual(Applicant.objects.count(), 0)
        self.assertEqual(Preference.objects.count(), 0)


# ---------------------------------------------------------------------------
# Facilities AJAX endpoint tests
# ---------------------------------------------------------------------------

class FacilitiesAPITests(TestCase):

    def setUp(self):
        _, self.taluka, self.f1, self.f2, self.f3 = make_master_data()
        self.url = reverse("portal:facilities-json")

    def test_no_taluka_param_returns_empty(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"facilities": []})

    def test_valid_taluka_returns_facilities(self):
        r = self.client.get(self.url, {"taluka": self.taluka.pk})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data["facilities"]), 3)
        names = {f["name"] for f in data["facilities"]}
        self.assertIn("PHC A", names)

    def test_facilities_include_vacancy_count(self):
        r = self.client.get(self.url, {"taluka": self.taluka.pk})
        f = next(f for f in r.json()["facilities"] if f["name"] == "PHC A")
        self.assertEqual(f["sanctioned_vacancies"], 2)

    def test_invalid_taluka_returns_404(self):
        r = self.client.get(self.url, {"taluka": 99999})
        self.assertEqual(r.status_code, 404)

    def test_post_not_allowed(self):
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, 405)


# ---------------------------------------------------------------------------
# Dashboard auth tests
# ---------------------------------------------------------------------------

class DashboardAuthTests(TestCase):

    def setUp(self):
        self.url = reverse("portal:dashboard")
        self.staff = User.objects.create_user(
            username="dho", password="secret", is_staff=True
        )

    def test_anonymous_redirected_to_login(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertIn("login", r["Location"])

    def test_staff_user_can_access(self):
        self.client.force_login(self.staff)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Placement Dashboard")

    def test_non_staff_user_redirected(self):
        non_staff = User.objects.create_user(username="applicant", password="secret")
        self.client.force_login(non_staff)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)


# ---------------------------------------------------------------------------
# Admin auth tests
# ---------------------------------------------------------------------------

class AdminAuthTests(TestCase):

    def test_anonymous_redirected_from_admin(self):
        r = self.client.get("/admin/portal/applicant/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("login", r["Location"])


# ---------------------------------------------------------------------------
# DB constraint tests
# ---------------------------------------------------------------------------

class ModelConstraintTests(TestCase):

    def setUp(self):
        self.qual, self.taluka, self.f1, self.f2, self.f3 = make_master_data()
        self.applicant = Applicant.objects.create(
            first_name="A", father_name="B", last_name="C",
            dob="1990-01-01", address="Addr", email="a@b.com", phone="9999999999",
            ug_qualification=self.qual, ug_score=80, score_type="PERCENTAGE",
        )

    def test_duplicate_email_raises_integrity_error(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Applicant.objects.create(
                first_name="X", father_name="Y", last_name="Z",
                dob="1990-01-01", address="Addr", email="a@b.com", phone="8888888888",
                ug_qualification=self.qual, ug_score=70, score_type="PERCENTAGE",
            )

    def test_duplicate_phone_raises_integrity_error(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Applicant.objects.create(
                first_name="X", father_name="Y", last_name="Z",
                dob="1990-01-01", address="Addr", email="other@b.com", phone="9999999999",
                ug_qualification=self.qual, ug_score=70, score_type="PERCENTAGE",
            )

    def test_duplicate_priority_raises_integrity_error(self):
        from django.db import IntegrityError
        Preference.objects.create(applicant=self.applicant, priority=1, facility=self.f1)
        with self.assertRaises(IntegrityError):
            Preference.objects.create(applicant=self.applicant, priority=1, facility=self.f2)

    def test_duplicate_facility_raises_integrity_error(self):
        from django.db import IntegrityError
        Preference.objects.create(applicant=self.applicant, priority=1, facility=self.f1)
        with self.assertRaises(IntegrityError):
            Preference.objects.create(applicant=self.applicant, priority=2, facility=self.f1)

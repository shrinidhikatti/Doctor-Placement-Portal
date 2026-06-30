import json

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, F as models_F, Q
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from .forms import ApplicantForm
from .models import Applicant, Facility, Preference, Taluka


def apply(request):
    if request.method == "POST":
        form = ApplicantForm(request.POST)
        if form.is_valid():
            applicant = form.save()
            return render(request, "portal/confirmation.html", {"applicant": applicant})
    else:
        form = ApplicantForm()
    return render(request, "portal/apply.html", {"form": form})


@staff_member_required
def dashboard(request):
    total = Applicant.objects.count()

    # Applications per taluka, measured by Priority-1 choices.
    taluka_demand = list(
        Preference.objects.filter(priority=1)
        .values(name=models_F("facility__taluka__name"))
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Per-facility demand broken down by priority, sorted by Priority-1 demand.
    facility_demand = [
        {
            "name": f.name,
            "type": f.type,
            "taluka_name": f.taluka.name,
            "sanctioned_vacancies": f.sanctioned_vacancies,
            "p1": f.p1,
            "p2": f.p2,
            "p3": f.p3,
        }
        for f in Facility.objects.annotate(
            p1=Count("preferences", filter=Q(preferences__priority=1)),
            p2=Count("preferences", filter=Q(preferences__priority=2)),
            p3=Count("preferences", filter=Q(preferences__priority=3)),
        )
        .filter(p1__gt=0)
        .select_related("taluka")
        .order_by("-p1")
    ]

    # Applications by UG qualification.
    by_qualification = list(
        Applicant.objects.values(name=models_F("ug_qualification__name"))
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Daily submission counts.
    daily_raw = list(
        Applicant.objects.annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )
    daily_labels = [str(r["date"]) for r in daily_raw]
    daily_counts = [r["count"] for r in daily_raw]

    return render(request, "portal/dashboard.html", {
        "total": total,
        "taluka_demand": taluka_demand,
        "facility_demand": facility_demand,
        "by_qualification": by_qualification,
        "taluka_labels_json": json.dumps([r["name"] for r in taluka_demand]),
        "taluka_counts_json": json.dumps([r["count"] for r in taluka_demand]),
        "qual_labels_json": json.dumps([r["name"] for r in by_qualification]),
        "qual_counts_json": json.dumps([r["count"] for r in by_qualification]),
        "daily_labels_json": json.dumps(daily_labels),
        "daily_counts_json": json.dumps(daily_counts),
    })


@require_GET
def facilities_json(request):
    """Return facilities for a taluka as JSON for the AJAX dependent dropdown."""
    taluka_id = request.GET.get("taluka")
    if not taluka_id:
        return JsonResponse({"facilities": []})
    get_object_or_404(Taluka, pk=taluka_id)
    facilities = (
        Facility.objects.filter(taluka_id=taluka_id)
        .values("id", "name", "type", "sanctioned_vacancies")
        .order_by("name")
    )
    return JsonResponse({"facilities": list(facilities)})

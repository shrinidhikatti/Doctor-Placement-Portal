import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from .forms import ApplicantForm
from .models import Facility, Taluka


def apply(request):
    if request.method == "POST":
        form = ApplicantForm(request.POST)
        if form.is_valid():
            applicant = form.save()
            return render(request, "portal/confirmation.html", {"applicant": applicant})
    else:
        form = ApplicantForm()
    return render(request, "portal/apply.html", {"form": form})


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

"""
Management command to load placeholder master data for development/testing.
Run: python manage.py seed_master_data

In production, load real talukas, facilities, and qualifications via the admin.
This command uses get_or_create so it is safe to run multiple times.
"""

from django.core.management.base import BaseCommand

from portal.models import Facility, Taluka, UGQualification


QUALIFICATIONS = ["MBBS", "BDS", "BAMS", "BHMS", "BUMS", "BNYS"]

TALUKAS = [
    "Belagavi", "Bailhongal", "Chikkodi", "Gokak",
    "Hukkeri", "Khanapur", "Raibag", "Ramdurg", "Savadatti",
]

# (taluka, facility_name, type, sanctioned_vacancies)
FACILITIES = [
    ("Belagavi",    "Kanabargi PHC",        "PHC", 2),
    ("Belagavi",    "Angol PHC",             "PHC", 1),
    ("Belagavi",    "Belagavi Urban CHC",    "CHC", 3),
    ("Bailhongal",  "Bailhongal PHC",        "PHC", 2),
    ("Bailhongal",  "Konnur PHC",            "PHC", 1),
    ("Bailhongal",  "Bailhongal CHC",        "CHC", 2),
    ("Gokak",       "Gokak CHC",             "CHC", 3),
    ("Gokak",       "Nandagad PHC",          "PHC", 1),
    ("Khanapur",    "Khanapur PHC",          "PHC", 2),
    ("Chikkodi",    "Chikkodi PHC",          "PHC", 1),
    ("Chikkodi",    "Chikkodi CHC",          "CHC", 2),
    ("Hukkeri",     "Hukkeri PHC",           "PHC", 1),
    ("Raibag",      "Raibag PHC",            "PHC", 2),
    ("Ramdurg",     "Ramdurg PHC",           "PHC", 1),
    ("Savadatti",   "Savadatti PHC",         "PHC", 2),
    ("Savadatti",   "Savadatti CHC",         "CHC", 1),
]


class Command(BaseCommand):
    help = "Load placeholder master data (qualifications, talukas, facilities) for testing."

    def handle(self, *args, **options):
        for name in QUALIFICATIONS:
            _, created = UGQualification.objects.get_or_create(name=name)
            if created:
                self.stdout.write(f"  + Qualification: {name}")

        taluka_map = {}
        for name in TALUKAS:
            t, created = Taluka.objects.get_or_create(name=name)
            taluka_map[name] = t
            if created:
                self.stdout.write(f"  + Taluka: {name}")

        for taluka_name, fname, ftype, vac in FACILITIES:
            _, created = Facility.objects.get_or_create(
                taluka=taluka_map[taluka_name],
                name=fname,
                type=ftype,
                defaults={"sanctioned_vacancies": vac},
            )
            if created:
                self.stdout.write(f"  + Facility: {fname} ({ftype}, {taluka_name})")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone — {UGQualification.objects.count()} qualifications, "
            f"{Taluka.objects.count()} talukas, "
            f"{Facility.objects.count()} facilities."
        ))

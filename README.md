# Doctor Placement Portal — Belagavi District

Django portal that captures UG graduate doctors' applications for CHC/PHC
postings, lets them submit 3 prioritised facility preferences, and gives the
DHO and CEO dashboards, reports, and Excel export. It **captures data and
generates reports** — it does not auto-allot postings.

See `docs/` for the full requirements specification and implementation plan.

## Stack
- Python 3.14, Django 6.0
- SQLite (local dev) / PostgreSQL (production, via `DATABASE_URL`)
- `django-import-export` (Excel export), WhiteNoise (static files)

## Local setup (Windows / PowerShell)

```powershell
# From the project root
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
copy .env.example .env   # then edit SECRET_KEY etc.

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/admin/ to log in.

## Project layout
```
config/        Django project (settings, urls, wsgi)
portal/        Main app
  models.py    UGQualification, Taluka, Facility, Applicant, Preference (spec §5)
  admin.py     DHO/CEO admin: list/search/filter, Preference inline, Excel export
  resources.py Excel/CSV export — flattens the 3 preferences into columns
docs/          Requirements spec + implementation plan
```

## Status (build phases from the implementation plan)
- [x] **Phase 0** — Project setup, venv, dependencies, settings, `.env`
- [x] **Phase 1** — Data model + migrations (master data still to be loaded)
- [~] **Phase 2** — Admin list/search/filter + Preference inline done; DHO/CEO
      users & "Officers" group still to be created
- [ ] **Phase 3** — Public application form + dependent taluka→facility dropdown
- [ ] **Phase 4** — Dashboard/reports (Excel export wiring is in place)
- [ ] **Phase 5** — Hardening & testing
- [ ] **Phase 6** — Deployment

## Next steps
1. Resolve the open decisions in `docs/01_requirements_specification.md` §9
   (UG qualification list, document uploads, application window, CEO
   permissions, edit-after-submit).
2. Load master data (UG qualifications, Belagavi talukas, facilities + vacancies).
3. Build the public form (Phase 3).

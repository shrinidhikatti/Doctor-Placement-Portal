# Doctor Placement Portal — Implementation Plan (Django)

A step-by-step build plan for a solo developer. Estimated total: **2–3 weeks** part-time. Each phase produces something working before you move on.

**Target stack**
- Python 3.12, Django 5.x
- PostgreSQL (production), SQLite is fine for local development
- `django-import-export` for Excel export
- Bootstrap 5 for the public form (CDN — no build step)
- Deployment: Render or Railway (both have free/cheap Postgres)

---

## Phase 0 — Setup (Day 1)

1. Install Python 3.12 and create a project folder.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```
3. Install packages:
   ```bash
   pip install django psycopg2-binary django-import-export python-decouple gunicorn whitenoise openpyxl
   ```
4. Start the project and the main app:
   ```bash
   django-admin startproject config .
   python manage.py startapp portal
   ```
5. Put secrets (SECRET_KEY, DB settings) in a `.env` file using `python-decouple`. Never commit `.env`.
6. Initialise git; add a `.gitignore` (venv, .env, __pycache__, db.sqlite3).

**Done when:** `python manage.py runserver` shows the Django welcome page.

---

## Phase 1 — Data Model & Master Data (Days 2–3)

1. Define the models in `portal/models.py`:
   - `UGQualification`, `Taluka`, `Facility`, `Applicant`, `Preference` (per the spec §5).
   - Add a unique constraint on `Applicant.email` and `Applicant.phone`.
   - Add `unique_together` / `UniqueConstraint` on `Preference` for (applicant, priority) and (applicant, facility).
2. Migrate:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
3. Register all models in `portal/admin.py`.
4. Create the superuser:
   ```bash
   python manage.py createsuperuser
   ```
5. **Load master data** via the admin panel (or a one-off script / Django fixture):
   - UG qualifications (your list).
   - All Belagavi talukas.
   - All PHCs/CHCs with their taluka and sanctioned vacancy count.

**Done when:** you can see and edit talukas, facilities, and vacancies inside `/admin`.

---

## Phase 2 — Admin Logins & Roles (Day 4)

1. Create two user accounts: **DHO** and **CEO** (mark them `staff`).
2. Create a Django **Group** (e.g., "Officers") with view/export permissions and add both users to it.
3. Customise the admin `Applicant` list:
   - `list_display`: name, phone, email, taluka of priority-1, UG qualification, created_at.
   - `search_fields`: name, phone, email.
   - `list_filter`: taluka, UG qualification.
   - Inline the `Preference` rows inside the applicant detail page.

**Done when:** DHO and CEO can each log in and browse all applications.

---

## Phase 3 — Public Application Form (Days 5–8) — *the main custom work*

1. Build the form (Django `ModelForm` for `Applicant` + a small formset or 3 fields for preferences).
2. Lock the **district** field to "Belagavi" (display as read-only / hidden value).
3. Build the **dependent dropdown**:
   - An API view, e.g. `GET /api/facilities/?taluka=<id>`, returns that taluka's facilities with name, type, and vacancy count as JSON.
   - On the page, when the taluka dropdown changes, a small JavaScript `fetch()` call populates the three priority dropdowns with those facilities (showing vacancies next to each).
4. Validation:
   - All required fields; valid email and 10-digit phone.
   - Priorities 1/2/3 must be distinct facilities.
   - Reject duplicate email/phone with a clear message.
5. On success: save applicant + 3 preferences in one transaction, then show a **confirmation page with a reference number**.
6. Style with Bootstrap 5; test on a phone screen.

**Done when:** a doctor can open the form on a phone, pick a taluka, see real vacancies, choose 3 priorities, and submit — and the record appears in admin.

---

## Phase 4 — Reports, Dashboard & Excel Export (Days 9–11)

1. **Excel export:** wire up `django-import-export` with a `Resource` for `Applicant` (flatten the 3 preferences into columns). Add the export button to the admin. Verify the downloaded `.xlsx` opens correctly.
2. **Dashboard page** (a simple staff-only view) showing:
   - Total applications.
   - Applications per taluka.
   - Priority-1 demand per facility, beside sanctioned vacancies.
   - Applications by UG qualification.
   - Daily applications during the window.
   Use Django ORM aggregations (`Count`, `annotate`) — render as tables plus a couple of Bootstrap/Chart.js bar charts.

**Done when:** DHO/CEO can download a complete Excel and see the dashboard numbers.

---

## Phase 5 — Hardening & Testing (Days 12–13)

1. Switch to PostgreSQL locally and confirm migrations run clean.
2. Turn off `DEBUG`; set `ALLOWED_HOSTS`; move `SECRET_KEY` to env.
3. Add `whitenoise` for static files.
4. Test the full flow end-to-end with 5–10 dummy applications, including duplicate and invalid-input cases.
5. Confirm only logged-in officers can reach admin/dashboard URLs.

**Done when:** the app runs in production mode with no debug, and all validation behaves correctly.

---

## Phase 6 — Deployment (Day 14)

1. Push the repo to GitHub.
2. Create a Render/Railway web service from the repo; add a Postgres instance.
3. Set environment variables (SECRET_KEY, DATABASE_URL, DEBUG=False, ALLOWED_HOSTS).
4. Run migrations on the server; `collectstatic`; create the DHO/CEO users; reload master data.
5. Enable automated database backups.
6. Add a custom domain + HTTPS (both providers give free SSL).

**Done when:** the public form URL works for applicants and the two officers can log in on the live site.

---

## Post-launch / optional later additions
- Document uploads (degree, ID proof).
- Auto-close the form after a deadline.
- Email/SMS confirmation to applicants.
- A "decision" field per applicant for DHO/CEO to record the final posting.

---

## Suggested order of priority if time is short
1. Data model + master data (Phase 1) — nothing works without it.
2. Public form + dependent dropdown (Phase 3) — your core feature.
3. Admin view + Excel export (Phases 2 & 4) — what DHO/CEO need.
4. Dashboard charts (Phase 4) — nice-to-have, can follow launch.

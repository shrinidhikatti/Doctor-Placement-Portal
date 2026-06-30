# Doctor Placement Portal — Requirements Specification

**Project:** CHC/PHC Doctor Placement Portal — Belagavi District
**Purpose:** Capture details of UG graduate doctors applying for postings at Community Health Centres (CHC) and Primary Health Centres (PHC), let them submit prioritised facility preferences, and give the DHO and CEO reports/exports to make the final posting decision manually.
**Stack:** Django (Python) + PostgreSQL, deployed on a commercial cloud.
**Scale:** ~100–500 applicants. (Small dataset — performance is a non-issue.)

---

## 1. Scope

The portal **captures data and generates reports**. It does **not** auto-allot postings. The DHO and CEO review the data and decide postings manually.

In scope:
- Public application form for graduate doctors.
- Master data for talukas, facilities (PHC/CHC) and their vacancies.
- Two admin logins (DHO, CEO) with dashboard, reports, and Excel export.

Out of scope (for now):
- Automated merit-based allotment.
- Payment/fees.
- SMS/email notifications (can be added later).

---

## 2. User Roles

| Role | Access | Can do |
|------|--------|--------|
| **Applicant (public)** | No login — open form | Fill and submit the application once; select 3 prioritised facilities. |
| **DHO** | Login | View all applications, filter/search, see dashboard, **download Excel of all details**. |
| **CEO** | Login | Same view as DHO (read + dashboard + export). Used for oversight and the joint posting decision. |

> Both DHO and CEO get the same capabilities for now. If you later want CEO to be read-only or to have an "approve" action, that's a small change.

---

## 3. Data to Capture (Application Form)

**Personal details**
- First name *(required)*
- Father's name *(required)*
- Last name *(required)*
- Date of birth *(required)*
- Correspondence address *(required)*
- Email ID *(required, valid email, unique)*
- Phone number *(required, 10 digits, unique)*

**Education**
- UG qualification — *dropdown from a list (list to be provided by you later)* *(required)*
- UG score — value *(required)*
- Score type — CGPA or Percentage *(required)*
- Higher qualification — *(optional, free text or dropdown)*

**Vacancy / Preference selection**
- District — **fixed to "Belagavi", displayed but frozen/non-editable**
- Taluka — dropdown *(required)*
- On taluka selection → show available PHCs and CHCs of that taluka **with their vacancy counts**
- Applicant selects **3 priorities** (Priority 1, 2, 3), each pointing to a facility
  - A facility cannot be chosen twice by the same applicant
  - Priorities must be distinct (1, 2, 3)

---

## 4. Master Data (set up before launch)

This is the backbone — load it first.

1. **UG Qualifications** — the list you will provide (e.g., MBBS, BDS, BAMS, etc.).
2. **Talukas** — all talukas of Belagavi district.
3. **Facilities** — each PHC/CHC, linked to its taluka, with:
   - Facility name
   - Type (PHC / CHC)
   - **Sanctioned vacancy count**

> **Note on vacancy display:** Show the *fixed sanctioned count*. Because posting is decided manually after the application window, vacancies should **not** decrement live, and multiple applicants choosing the same facility as Priority 1 is expected and fine.

---

## 5. Data Model (tables)

1. **UGQualification** — `id`, `name`
2. **Taluka** — `id`, `name`
3. **Facility** — `id`, `taluka (FK)`, `name`, `type` (PHC/CHC), `sanctioned_vacancies`
4. **Applicant** — `id`, `first_name`, `father_name`, `last_name`, `dob`, `address`, `email` (unique), `phone` (unique), `ug_qualification (FK)`, `ug_score`, `score_type` (CGPA/Percentage), `higher_qualification` (nullable), `created_at`
5. **Preference** — `id`, `applicant (FK)`, `priority` (1/2/3), `facility (FK)`
   - Constraint: unique (`applicant`, `priority`) and unique (`applicant`, `facility`)
6. **User** — Django's built-in auth, with two accounts (DHO, CEO) in a staff group.

---

## 6. Functional Requirements

**Public form**
- Single page, mobile-friendly (applicants will use phones).
- Dependent dropdown: selecting a taluka loads that taluka's facilities + vacancies via AJAX.
- Validation: required fields, valid email/phone, distinct priorities.
- Duplicate prevention: block a second submission with the same email or phone.
- Confirmation screen / reference number after submit.

**Admin (DHO / CEO)**
- Secure login.
- List view of all applicants with search (name, phone, email) and filters (taluka, UG qualification, priority-1 facility).
- Detail view showing an applicant's full record including their 3 preferences.
- **Excel export** of all applicants and their preferences (one click).
- **Dashboard** with key reports (see §7).

---

## 7. Dashboard / Reports

Useful, low-effort reports to include:
- Total applications received.
- Applications per taluka (which talukas are most contested).
- Demand per facility — count of applicants who picked each facility as Priority 1 / 2 / 3 (helps the manual posting decision).
- Vacancies vs. demand per facility (sanctioned count beside Priority-1 demand).
- Applications by UG qualification.
- Applications over time (daily count during the window).

All of the above are simple counts — easy to render as tables and a few bar charts.

---

## 8. Non-Functional Requirements

- **Validation & integrity:** server-side validation on every field; DB-level unique constraints on email and phone.
- **Security:** HTTPS, Django's CSRF protection, strong admin passwords, no public access to admin URLs without login.
- **Backups:** enable automated DB backups on the cloud provider.
- **Audit:** `created_at` timestamp on every application; consider keeping admin login records.
- **Privacy:** this is personal data of applicants — restrict access to DHO/CEO only and don't expose it publicly.

---

## 9. Open Decisions (confirm before/while building)

1. **UG qualification list** — you'll provide this.
2. **Document uploads** — do you need degree certificate / ID proof / internship completion uploaded? (Not in the original plan; decide now if needed, as it affects the form and storage.)
3. **Application window** — should the form auto-close after a deadline?
4. **CEO permissions** — same as DHO, or read-only?
5. **Edit after submit** — can an applicant edit their submission, or is it final once submitted?

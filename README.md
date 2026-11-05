# CareLedger clinic records

An early Django implementation of the doctor and staff workflow for `srilasya-08/hospital-records-manager`.

## What is here

- Role-aware sign-in and separate doctor and staff workspaces.
- Doctor patient search and record view, patient creation, and staff upload-task assignment.
- Staff can see only open tasks assigned to their account. Task forms omit patient demographics and existing chart information. Every task lookup is filtered by the signed-in staff account on the server.
- Staff can enter visit date, temperature, next recommended visit, visit notes, and a PDF/PNG/JPEG upload. Submissions become unavailable for further staff editing.
- Doctors can review the visit and save diagnosis, prescription, and treatment plan.
- Document downloads go through a doctor-only view; uploads are stored outside the static site directory.
- UUIDs are used for patient and task URLs, while server-side permission checks remain authoritative.

## Local setup

Use Python 3.11 or later. Create a virtual environment, install `requirements.txt`, copy `.env.example` to `.env`, and set a long random `DJANGO_SECRET_KEY`. For local-only development the app can use SQLite by leaving `DATABASE_URL` blank. Use a managed PostgreSQL database for any shared environment. Keep `.env` and `private_uploads/` out of Git.

Then run:

```text
python manage.py migrate
python manage.py create_clinic_user doctor1 --role Doctor
python manage.py create_clinic_user staff1 --role Staff
python manage.py runserver
```

The login page is at `/accounts/login/`. The first doctor can create patient records and assign upload tasks. `create_clinic_user` prompts for each password rather than putting it in shell history.

## Before handling real patient records

This is an implementation starting point, not a production-ready medical records service. Before using real data, add a second-person security review, MFA, malware scanning, managed private object storage, encrypted backups and recovery checks, stronger account lifecycle controls, and a compliance review for the clinic's operating jurisdiction. Configure HTTPS, secrets, database backups, retention rules, monitoring, and incident response in the hosting environment. Confirm legal/privacy notices and patient consent requirements with qualified local counsel. Do not use real patient data in development or test environments.

Current file validation checks size, extension, and common file signatures. It does not replace antivirus scanning or a dedicated private file storage service. Audit events record basic actions but are not tamper-proof or a complete access history yet.

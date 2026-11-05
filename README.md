# CareLedger inpatient records

A Django application for staff-entered inpatient records and doctor review.

## Current workflow

- Staff create patient and admission records directly, without waiting for a doctor to create a task.
- Staff can list and update only patient records created by their own account. Doctor accounts can browse all patient records. Access checks run on the server for each request.
- Patient information includes name, place, phone, age, date of birth, allergy status/details, room, admission date, and optional discharge date.
- Staff enter dated temperature, height, weight, free-text symptoms, and a yes/no/not-recorded vomiting response with duration.
- Prescription, X-ray, blood test, ultrasound, extra scan, and other test files each have a separate upload slot. Test uploads require their test date. Empty categories display that no file was uploaded.
- Staff can add medicine entries with medicine name, administrator name, and administration date/time; they can also record doctor name, visit date/time, and notes.
- Doctors can view all of the above and add diagnosis, prescription notes, and treatment plan to visit entries.
- Files are served through an authenticated download view and stored outside the static web directory.

## Local setup

Use Python 3.11 or later. Create a virtual environment and install the dependencies:

```powershell
py -3.13 -m venv .venv
$python = Join-Path $PWD ".venv\Scripts\python.exe"
& $python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

For local development, edit `.env`: set a long random `DJANGO_SECRET_KEY`, set `DJANGO_DEBUG=true`, and leave `DATABASE_URL` blank to use SQLite. `DJANGO_DEBUG=true` is for local use only; it enables HTTP and static file serving for Django's development server. Keep `.env` and `private_uploads/` out of Git.

Create the local database and two login accounts:

```powershell
& $python manage.py migrate
& $python manage.py create_clinic_user doctor1 --role Doctor
& $python manage.py create_clinic_user staff1 --role Staff
& $python manage.py runserver
```

The account command prompts for a password. Open http://127.0.0.1:8000/accounts/login/ to sign in. Staff and doctor accounts are provisioned with the `create_clinic_user` command.

For a shared environment, set `DJANGO_DEBUG=false`, use a managed PostgreSQL database with SSL, and use private managed file storage. Do not use the development server for deployment.

## Before handling real patient records

This is an early implementation, not a production-ready medical records service. Before real use, complete a security review, add MFA and account lifecycle controls, virus scanning, managed private file storage, encrypted backups and recovery checks, reliable audit logging, retention controls, monitoring, and incident response. Configure HTTPS, secrets, database backups, and privacy notices in the hosting environment. Confirm local legal and patient-consent requirements with qualified counsel. Use only synthetic data during development.

File validation checks file size, extension, and common file signatures. It does not replace malware scanning. The audit log is a basic event trail; it is not tamper-proof or a complete access history.

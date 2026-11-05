from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import AssignVisitTaskForm, DoctorVisitForm, PatientAndTaskForm, StaffVisitForm
from .models import AuditEvent, Patient, UploadTask, Visit, VisitDocument
from .permissions import has_role, role_required


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if has_role(request.user, "Staff"):
        return redirect("staff_tasks")
    if has_role(request.user, "Doctor"):
        return redirect("patient_list")
    return render(request, "clinic/unauthorized.html", status=403)


@role_required("Staff")
def staff_tasks(request):
    tasks = UploadTask.objects.filter(assigned_to=request.user, status__in=["open", "correction"], visit__patient_id=F("patient_id"))
    return render(request, "clinic/staff_tasks.html", {"tasks": tasks})


@role_required("Staff")
def staff_task(request, task_code):
    task = get_object_or_404(UploadTask.objects.filter(assigned_to=request.user, status__in=["open", "correction"], visit__patient_id=F("patient_id")), task_code=task_code)
    if request.method == "POST":
        form = StaffVisitForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                visit = task.visit
                visit.visit_date = form.cleaned_data["visit_date"]
                visit.temperature_c = form.cleaned_data["temperature_c"]
                visit.next_recommended_visit = form.cleaned_data["next_recommended_visit"]
                visit.staff_notes = form.cleaned_data["staff_notes"]
                visit.created_by = request.user
                visit.save(update_fields=["visit_date", "temperature_c", "next_recommended_visit", "staff_notes", "created_by"])
                if form.cleaned_data["document"]:
                    VisitDocument.objects.create(visit=visit, uploaded_by=request.user,
                        title=form.cleaned_data["document_title"] or "Visit document", file=form.cleaned_data["document"])
                task.status = "submitted"
                task.submitted_at = timezone.now()
                task.save(update_fields=["status", "submitted_at"])
                AuditEvent.objects.create(actor=request.user, action="staff_task_submitted", object_type="visit", object_id=str(visit.pk))
            messages.success(request, "Visit details submitted to the doctor.")
            return redirect("staff_tasks")
    else:
        form = StaffVisitForm()
    # Do not expose patient demographics, existing chart, visit history, diagnosis, or prescription.
    return render(request, "clinic/staff_task.html", {"task": task, "form": form})


@role_required("Doctor")
def patient_list(request):
    patients = Patient.objects.order_by("full_name")
    query = request.GET.get("q", "").strip()
    if query:
        patients = patients.filter(full_name__icontains=query)
    return render(request, "clinic/patient_list.html", {"patients": patients, "query": query})


@role_required("Doctor")
def patient_create(request):
    if request.method == "POST":
        form = PatientAndTaskForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                patient = Patient.objects.create(full_name=form.cleaned_data["full_name"],
                    date_of_birth=form.cleaned_data["date_of_birth"], phone=form.cleaned_data["phone"])
                visit = Visit.objects.create(patient=patient, visit_number=1,
                    visit_date=form.cleaned_data["visit_date"], created_by=request.user)
                task = UploadTask.objects.create(patient=patient, visit=visit,
                    assigned_to=form.cleaned_data["assigned_to"])
                AuditEvent.objects.create(actor=request.user, action="patient_created", object_type="patient", object_id=str(patient.pk))
                AuditEvent.objects.create(actor=request.user, action="upload_task_assigned", object_type="upload_task", object_id=str(task.pk))
            messages.success(request, "Patient record created and staff upload task assigned.")
            return redirect("patient_detail", public_id=patient.public_id)
    else:
        form = PatientAndTaskForm()
    return render(request, "clinic/patient_create.html", {"form": form})


@role_required("Doctor")
def new_visit_task(request, public_id):
    patient = get_object_or_404(Patient, public_id=public_id)
    if request.method == "POST":
        form = AssignVisitTaskForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                latest = patient.visits.order_by("-visit_number").values_list("visit_number", flat=True).first() or 0
                visit = Visit.objects.create(patient=patient, visit_number=latest + 1,
                    visit_date=form.cleaned_data["visit_date"], created_by=request.user)
                task = UploadTask.objects.create(patient=patient, visit=visit,
                    assigned_to=form.cleaned_data["assigned_to"])
                AuditEvent.objects.create(actor=request.user, action="upload_task_assigned", object_type="upload_task", object_id=str(task.pk))
            messages.success(request, f"Visit {visit.visit_number} created and assigned to staff.")
            return redirect("patient_detail", public_id=patient.public_id)
    else:
        form = AssignVisitTaskForm()
    return render(request, "clinic/new_visit_task.html", {"patient": patient, "form": form})


@role_required("Doctor")
def patient_detail(request, public_id):
    patient = get_object_or_404(Patient, public_id=public_id)
    visits = patient.visits.prefetch_related("documents").all()
    bound_form = None
    bound_visit_id = None
    if request.method == "POST":
        visit_id = request.POST.get("visit_id")
        visit = get_object_or_404(visits, pk=visit_id)
        form = DoctorVisitForm(request.POST)
        if form.is_valid():
            visit.diagnosis = form.cleaned_data["diagnosis"]
            visit.prescription = form.cleaned_data["prescription"]
            visit.treatment_plan = form.cleaned_data["treatment_plan"]
            visit.reviewed_by = request.user
            visit.reviewed_at = timezone.now()
            visit.save(update_fields=["diagnosis", "prescription", "treatment_plan", "reviewed_by", "reviewed_at"])
            task = getattr(visit, "upload_task", None)
            if task:
                task.status = "submitted"
                task.save(update_fields=["status"])
            AuditEvent.objects.create(actor=request.user, action="doctor_visit_updated", object_type="visit", object_id=str(visit.pk))
            messages.success(request, "Clinical note saved.")
            return redirect("patient_detail", public_id=patient.public_id)
        bound_form, bound_visit_id = form, visit.pk
    visit_items = []
    for visit in visits:
        initial = {"diagnosis": visit.diagnosis, "prescription": visit.prescription, "treatment_plan": visit.treatment_plan}
        visit_items.append({"visit": visit, "form": bound_form if bound_visit_id == visit.pk else DoctorVisitForm(initial=initial)})
    return render(request, "clinic/patient_detail.html", {"patient": patient, "visit_items": visit_items})


@role_required("Doctor")
def document_download(request, document_id):
    document = get_object_or_404(VisitDocument.objects.select_related("visit"), pk=document_id)
    AuditEvent.objects.create(actor=request.user, action="document_downloaded", object_type="visit_document", object_id=str(document.pk))
    try:
        return FileResponse(document.file.open("rb"), as_attachment=True, filename=document.title)
    except FileNotFoundError:
        raise Http404

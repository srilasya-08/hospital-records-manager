from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (DischargeDateForm, DoctorVisitForm, DoctorVisitLogForm, FILE_FIELDS, MedicineAdministrationForm,
                    RecordDocumentsForm, StaffPatientCreateForm, VisitEntryForm)
from .models import Admission, AuditEvent, DoctorVisit, MedicineAdministration, Patient, Visit, VisitDocument
from .permissions import has_role, role_required


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if has_role(request.user, "Staff"):
        return redirect("staff_patient_list")
    if has_role(request.user, "Doctor"):
        return redirect("patient_list")
    return render(request, "clinic/unauthorized.html", status=403)


@role_required("Staff")
def staff_patient_list(request):
    patients = Patient.objects.filter(created_by=request.user).order_by("full_name")
    query = request.GET.get("q", "").strip()
    if query:
        patients = patients.filter(full_name__icontains=query)
    return render(request, "clinic/staff_patients.html", {"patients": patients, "query": query})


def save_documents(form, visit, user):
    for field_name, (category, label) in FILE_FIELDS.items():
        uploaded = form.cleaned_data.get(field_name)
        if uploaded:
            test_date = None if category == "prescription" else form.cleaned_data.get(f"{category}_date")
            VisitDocument.objects.create(visit=visit, uploaded_by=user, category=category,
                test_date=test_date, title=label, file=uploaded)


def bool_or_none(choice):
    if choice == "yes":
        return True
    if choice == "no":
        return False
    return None


@role_required("Staff")
def staff_patient_create(request):
    if request.method == "POST":
        form = StaffPatientCreateForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                patient = Patient.objects.create(
                    full_name=form.cleaned_data["full_name"], place=form.cleaned_data["place"],
                    phone=form.cleaned_data["phone"], age=form.cleaned_data["age"],
                    date_of_birth=form.cleaned_data["date_of_birth"],
                    allergy_status=form.cleaned_data["allergy_status"], allergies=form.cleaned_data["allergies"],
                    created_by=request.user)
                admission = Admission.objects.create(patient=patient, room_number=form.cleaned_data["room_number"],
                    admitted_on=form.cleaned_data["admitted_on"], created_by=request.user)
                visit = Visit.objects.create(patient=patient, admission=admission, visit_number=1,
                    visit_date=form.cleaned_data["visit_date"], temperature_c=form.cleaned_data["temperature_c"],
                    height_cm=form.cleaned_data["height_cm"], weight_kg=form.cleaned_data["weight_kg"],
                    other_symptoms=form.cleaned_data["other_symptoms"], vomiting=bool_or_none(form.cleaned_data["vomiting"]),
                    vomiting_days=form.cleaned_data["vomiting_days"], created_by=request.user)
                save_documents(form, visit, request.user)
                AuditEvent.objects.create(actor=request.user, action="staff_patient_created", object_type="patient", object_id=str(patient.pk))
            messages.success(request, "Patient and admission record created.")
            return redirect("staff_patient_detail", public_id=patient.public_id)
    else:
        form = StaffPatientCreateForm(initial={"admitted_on": timezone.localdate(), "visit_date": timezone.localdate()})
    return render(request, "clinic/staff_patient_create.html", {"form": form})


def patient_context(patient, staff_view=False):
    admissions = patient.admissions.prefetch_related("medicines", "doctor_visits").all()
    latest_admission = admissions.first()
    visits = patient.visits.prefetch_related("documents").all()
    all_documents = VisitDocument.objects.filter(visit__patient=patient).select_related("visit").order_by("-test_date", "-uploaded_at")
    document_groups = [{"category": category, "label": label,
        "documents": [doc for doc in all_documents if doc.category == category]}
        for category, label in VisitDocument.CATEGORIES]
    return {
        "patient": patient, "admissions": admissions, "visits": visits,
        "latest_admission": latest_admission,
        "active_admission": latest_admission if latest_admission and not latest_admission.discharge_date else None,
        "medicine_form": MedicineAdministrationForm(), "doctor_visit_form": DoctorVisitLogForm(),
        "entry_form": VisitEntryForm(initial={"visit_date": timezone.localdate()}),
        "documents_form": RecordDocumentsForm(), "discharge_form": DischargeDateForm(),
        "document_groups": document_groups, "staff_view": staff_view,
    }


@role_required("Staff")
def staff_patient_detail(request, public_id):
    patient = get_object_or_404(Patient.objects.filter(created_by=request.user), public_id=public_id)
    if request.method == "POST":
        admission = patient.admissions.order_by("-admitted_on", "-id").first()
        if not admission:
            raise Http404
        action = request.POST.get("action")
        bound_form = None
        if action in {"entry", "medicine", "doctor_visit", "documents"} and admission.discharge_date:
            messages.error(request, "This admission is discharged and can’t receive new entries.")
            return redirect("staff_patient_detail", public_id=patient.public_id)
        if action == "entry":
            form = VisitEntryForm(request.POST)
            bound_form = ("entry_form", form)
            if form.is_valid():
                latest = patient.visits.order_by("-visit_number").values_list("visit_number", flat=True).first() or 0
                Visit.objects.create(patient=patient, admission=admission, visit_number=latest + 1,
                    visit_date=form.cleaned_data["visit_date"], temperature_c=form.cleaned_data["temperature_c"],
                    height_cm=form.cleaned_data["height_cm"], weight_kg=form.cleaned_data["weight_kg"],
                    other_symptoms=form.cleaned_data["other_symptoms"], vomiting=bool_or_none(form.cleaned_data["vomiting"]),
                    vomiting_days=form.cleaned_data["vomiting_days"], created_by=request.user)
                AuditEvent.objects.create(actor=request.user, action="visit_entry_created", object_type="patient", object_id=str(patient.pk))
                messages.success(request, "Visit details added.")
                return redirect("staff_patient_detail", public_id=patient.public_id)
        elif action == "medicine":
            form = MedicineAdministrationForm(request.POST)
            bound_form = ("medicine_form", form)
            if form.is_valid():
                MedicineAdministration.objects.create(admission=admission, entered_by=request.user, **form.cleaned_data)
                AuditEvent.objects.create(actor=request.user, action="medicine_administration_recorded", object_type="admission", object_id=str(admission.pk))
                messages.success(request, "Medicine administration recorded.")
                return redirect("staff_patient_detail", public_id=patient.public_id)
        elif action == "doctor_visit":
            form = DoctorVisitLogForm(request.POST)
            bound_form = ("doctor_visit_form", form)
            if form.is_valid():
                DoctorVisit.objects.create(admission=admission, entered_by=request.user, **form.cleaned_data)
                AuditEvent.objects.create(actor=request.user, action="doctor_visit_recorded", object_type="admission", object_id=str(admission.pk))
                messages.success(request, "Doctor visit recorded.")
                return redirect("staff_patient_detail", public_id=patient.public_id)
        elif action == "documents":
            form = RecordDocumentsForm(request.POST, request.FILES)
            bound_form = ("documents_form", form)
            if form.is_valid():
                visit = patient.visits.order_by("-visit_number").first()
                if not visit:
                    raise Http404
                save_documents(form, visit, request.user)
                AuditEvent.objects.create(actor=request.user, action="patient_documents_uploaded", object_type="patient", object_id=str(patient.pk))
                messages.success(request, "Documents uploaded.")
                return redirect("staff_patient_detail", public_id=patient.public_id)
        elif action == "discharge":
            form = DischargeDateForm(request.POST)
            bound_form = ("discharge_form", form)
            if form.is_valid() and form.cleaned_data["discharge_date"] < admission.admitted_on:
                form.add_error("discharge_date", "Discharge date cannot be before the admission date.")
            if form.is_valid():
                admission.discharge_date = form.cleaned_data["discharge_date"]
                admission.save(update_fields=["discharge_date"])
                AuditEvent.objects.create(actor=request.user, action="patient_discharged", object_type="admission", object_id=str(admission.pk))
                messages.success(request, "Discharge date saved.")
                return redirect("staff_patient_detail", public_id=patient.public_id)
        else:
            raise Http404
        context = patient_context(patient, staff_view=True)
        if bound_form:
            context[bound_form[0]] = bound_form[1]
        return render(request, "clinic/staff_patient_detail.html", context)
    return render(request, "clinic/staff_patient_detail.html", patient_context(patient, staff_view=True))


@role_required("Doctor")
def patient_list(request):
    patients = Patient.objects.order_by("full_name")
    query = request.GET.get("q", "").strip()
    if query:
        patients = patients.filter(full_name__icontains=query)
    return render(request, "clinic/patient_list.html", {"patients": patients, "query": query})


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
            AuditEvent.objects.create(actor=request.user, action="doctor_visit_updated", object_type="visit", object_id=str(visit.pk))
            messages.success(request, "Clinical note saved.")
            return redirect("patient_detail", public_id=patient.public_id)
        bound_form, bound_visit_id = form, visit.pk
    context = patient_context(patient)
    context["visit_items"] = []
    for visit in visits:
        initial = {"diagnosis": visit.diagnosis, "prescription": visit.prescription, "treatment_plan": visit.treatment_plan}
        context["visit_items"].append({"visit": visit, "form": bound_form if bound_visit_id == visit.pk else DoctorVisitForm(initial=initial)})
    return render(request, "clinic/patient_detail.html", context)


@login_required
def document_download(request, document_id):
    if request.user.groups.filter(name__in=["Doctor", "Staff"]).count() != 1:
        raise PermissionDenied
    document = get_object_or_404(VisitDocument.objects.select_related("visit__patient"), pk=document_id)
    if has_role(request.user, "Staff") and document.visit.patient.created_by_id != request.user.id:
        raise Http404
    AuditEvent.objects.create(actor=request.user, action="document_downloaded", object_type="visit_document", object_id=str(document.pk))
    try:
        return FileResponse(document.file.open("rb"), as_attachment=True, filename=document.title)
    except FileNotFoundError:
        raise Http404

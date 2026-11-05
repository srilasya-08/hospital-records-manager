import uuid

from django.conf import settings
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models


class Patient(models.Model):
    ALLERGY_STATUS = [("unknown", "Not yet checked"), ("none_known", "No known allergies"), ("recorded", "Allergies recorded")]
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    full_name = models.CharField(max_length=160)
    place = models.CharField(max_length=160, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    age = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MaxValueValidator(130)])
    date_of_birth = models.DateField(null=True, blank=True)
    allergy_status = models.CharField(max_length=16, choices=ALLERGY_STATUS, default="unknown")
    allergies = models.TextField(blank=True, help_text="Allergy and reaction details, when known.")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="registered_patients")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({str(self.public_id)[:8]})"


class Admission(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="admissions")
    room_number = models.CharField(max_length=40, blank=True)
    admitted_on = models.DateField()
    discharge_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_admissions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-admitted_on", "-id"]


class Visit(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="visits")
    admission = models.ForeignKey(Admission, on_delete=models.PROTECT, null=True, blank=True, related_name="visits")
    visit_number = models.PositiveIntegerField()
    visit_date = models.DateField()
    temperature_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(25), MaxValueValidator(45)])
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(260)])
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(0.5), MaxValueValidator(500)])
    other_symptoms = models.TextField(blank=True)
    vomiting = models.BooleanField(null=True, blank=True)
    vomiting_days = models.PositiveSmallIntegerField(null=True, blank=True)
    diagnosis = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
    treatment_plan = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_visits")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="reviewed_visits")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["patient", "visit_number"], name="unique_patient_visit_number")]
        ordering = ["-visit_date", "-id"]


class VisitDocument(models.Model):
    CATEGORIES = [
        ("prescription", "Prescription"), ("xray", "X-ray"), ("blood_test", "Blood test"),
        ("ultrasound", "Ultrasound"), ("extra_scan", "Extra scan"), ("extra_test", "Other test"),
    ]
    visit = models.ForeignKey(Visit, on_delete=models.PROTECT, related_name="documents")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    category = models.CharField(max_length=20, choices=CATEGORIES, default="extra_test")
    test_date = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=160)
    file = models.FileField(upload_to="records/%Y/%m/", validators=[FileExtensionValidator(["pdf", "png", "jpg", "jpeg"])])
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["category", "-test_date", "-uploaded_at"]


class MedicineAdministration(models.Model):
    admission = models.ForeignKey(Admission, on_delete=models.PROTECT, related_name="medicines")
    medicine_name = models.CharField(max_length=200)
    administered_by_name = models.CharField(max_length=160)
    administered_at = models.DateTimeField()
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-administered_at"]


class DoctorVisit(models.Model):
    admission = models.ForeignKey(Admission, on_delete=models.PROTECT, related_name="doctor_visits")
    doctor_name = models.CharField(max_length=160)
    visited_at = models.DateTimeField()
    notes = models.TextField(blank=True)
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-visited_at"]


class UploadTask(models.Model):
    """Legacy workflow model retained for existing local databases."""
    STATUS_CHOICES = [("open", "Open"), ("submitted", "Submitted"), ("correction", "Correction requested")]
    task_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="upload_tasks")
    visit = models.OneToOneField(Visit, on_delete=models.PROTECT, related_name="upload_task")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="upload_tasks")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]


class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=64)
    object_type = models.CharField(max_length=64)
    object_id = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

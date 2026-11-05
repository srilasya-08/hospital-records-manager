import uuid
from django.conf import settings
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models


class Patient(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    full_name = models.CharField(max_length=160)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({str(self.public_id)[:8]})"


class Visit(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="visits")
    visit_number = models.PositiveIntegerField()
    visit_date = models.DateField()
    temperature_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(25), MaxValueValidator(45)])
    next_recommended_visit = models.DateField(null=True, blank=True)
    staff_notes = models.TextField(blank=True)
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


class UploadTask(models.Model):
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


class VisitDocument(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.PROTECT, related_name="documents")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    title = models.CharField(max_length=160)
    file = models.FileField(upload_to="records/%Y/%m/", validators=[FileExtensionValidator(["pdf", "png", "jpg", "jpeg"])])
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=64)
    object_type = models.CharField(max_length=64)
    object_id = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)
    # Intentionally excludes clinical content, credentials, tokens, and file names.

    class Meta:
        ordering = ["-created_at"]

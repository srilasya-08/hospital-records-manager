import uuid
from django.conf import settings
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="Patient", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ("full_name", models.CharField(max_length=160)),
            ("date_of_birth", models.DateField(blank=True, null=True)),
            ("phone", models.CharField(blank=True, max_length=32)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name="Visit", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("visit_number", models.PositiveIntegerField()),
            ("visit_date", models.DateField()),
            ("temperature_c", models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True, validators=[MinValueValidator(25), MaxValueValidator(45)])),
            ("next_recommended_visit", models.DateField(blank=True, null=True)),
            ("staff_notes", models.TextField(blank=True)),
            ("diagnosis", models.TextField(blank=True)),
            ("prescription", models.TextField(blank=True)),
            ("treatment_plan", models.TextField(blank=True)),
            ("reviewed_at", models.DateTimeField(blank=True, null=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_visits", to=settings.AUTH_USER_MODEL)),
            ("patient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="visits", to="clinic.patient")),
            ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="reviewed_visits", to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ["-visit_date", "-id"]}),
        migrations.CreateModel(name="UploadTask", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("task_code", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ("status", models.CharField(choices=[("open", "Open"), ("submitted", "Submitted"), ("correction", "Correction requested")], default="open", max_length=16)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("submitted_at", models.DateTimeField(blank=True, null=True)),
            ("assigned_to", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="upload_tasks", to=settings.AUTH_USER_MODEL)),
            ("patient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="upload_tasks", to="clinic.patient")),
            ("visit", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="upload_task", to="clinic.visit")),
        ], options={"ordering": ["created_at"]}),
        migrations.CreateModel(name="VisitDocument", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("title", models.CharField(max_length=160)),
            ("file", models.FileField(upload_to="records/%Y/%m/", validators=[FileExtensionValidator(["pdf", "png", "jpg", "jpeg"])])),
            ("uploaded_at", models.DateTimeField(auto_now_add=True)),
            ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ("visit", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="documents", to="clinic.visit")),
        ]),
        migrations.CreateModel(name="AuditEvent", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("action", models.CharField(max_length=64)),
            ("object_type", models.CharField(max_length=64)),
            ("object_id", models.CharField(max_length=80)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ["-created_at"]}),
        migrations.AddConstraint(model_name="visit", constraint=models.UniqueConstraint(fields=("patient", "visit_number"), name="unique_patient_visit_number")),
    ]

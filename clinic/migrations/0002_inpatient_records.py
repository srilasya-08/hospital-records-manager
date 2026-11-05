from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("clinic", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.AddField("patient", "place", models.CharField(blank=True, max_length=160)),
        migrations.AddField("patient", "age", models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(130)])),
        migrations.AddField("patient", "allergy_status", models.CharField(choices=[("unknown", "Not yet checked"), ("none_known", "No known allergies"), ("recorded", "Allergies recorded")], default="unknown", max_length=16)),
        migrations.AddField("patient", "allergies", models.TextField(blank=True, help_text="Allergy and reaction details, when known.")),
        migrations.AddField("patient", "created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="registered_patients", to=settings.AUTH_USER_MODEL)),
        migrations.CreateModel(name="Admission", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("room_number", models.CharField(blank=True, max_length=40)),
            ("admitted_on", models.DateField()),
            ("discharge_date", models.DateField(blank=True, null=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_admissions", to=settings.AUTH_USER_MODEL)),
            ("patient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="admissions", to="clinic.patient")),
        ], options={"ordering": ["-admitted_on", "-id"]}),
        migrations.AddField("visit", "admission", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="visits", to="clinic.admission")),
        migrations.AddField("visit", "height_cm", models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True, validators=[MinValueValidator(20), MaxValueValidator(260)])),
        migrations.AddField("visit", "weight_kg", models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True, validators=[MinValueValidator(0.5), MaxValueValidator(500)])),
        migrations.AddField("visit", "other_symptoms", models.TextField(blank=True)),
        migrations.AddField("visit", "vomiting", models.BooleanField(blank=True, null=True)),
        migrations.AddField("visit", "vomiting_days", models.PositiveSmallIntegerField(blank=True, null=True)),
        migrations.AddField("visitdocument", "category", models.CharField(choices=[("prescription", "Prescription"), ("xray", "X-ray"), ("blood_test", "Blood test"), ("ultrasound", "Ultrasound"), ("extra_scan", "Extra scan"), ("extra_test", "Other test")], default="extra_test", max_length=20)),
        migrations.AddField("visitdocument", "test_date", models.DateField(blank=True, null=True)),
        migrations.CreateModel(name="MedicineAdministration", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("medicine_name", models.CharField(max_length=200)),
            ("administered_by_name", models.CharField(max_length=160)),
            ("administered_at", models.DateTimeField()),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("admission", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="medicines", to="clinic.admission")),
            ("entered_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ["-administered_at"]}),
        migrations.CreateModel(name="DoctorVisit", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("doctor_name", models.CharField(max_length=160)),
            ("visited_at", models.DateTimeField()),
            ("notes", models.TextField(blank=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("admission", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="doctor_visits", to="clinic.admission")),
            ("entered_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ["-visited_at"]}),
    ]

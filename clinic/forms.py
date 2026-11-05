from django import forms
from django.core.exceptions import ValidationError

from .models import Patient, VisitDocument

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
FILE_FIELDS = {
    "prescription_file": ("prescription", "Prescription"),
    "xray_file": ("xray", "X-ray"),
    "blood_test_file": ("blood_test", "Blood test"),
    "ultrasound_file": ("ultrasound", "Ultrasound"),
    "extra_scan_file": ("extra_scan", "Extra scan"),
    "extra_test_file": ("extra_test", "Other test"),
}


class SecureUploadField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("widget", forms.ClearableFileInput(attrs={"accept": ".pdf,.png,.jpg,.jpeg"}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        uploaded = super().clean(data, initial)
        if uploaded:
            if uploaded.size > MAX_UPLOAD_BYTES:
                raise ValidationError("File must be smaller than 15 MB.")
            header = uploaded.read(8)
            uploaded.seek(0)
            valid = (
                (uploaded.name.lower().endswith(".pdf") and header.startswith(b"%PDF-"))
                or (uploaded.name.lower().endswith(".png") and header.startswith(b"\x89PNG\r\n\x1a\n"))
                or (uploaded.name.lower().endswith((".jpg", ".jpeg")) and header.startswith(b"\xff\xd8\xff"))
            )
            if not valid:
                raise ValidationError("Upload a PDF, PNG, or JPEG file.")
        return uploaded


class StaffPatientCreateForm(forms.Form):
    full_name = forms.CharField(max_length=160, label="Patient name")
    place = forms.CharField(max_length=160, required=False)
    phone = forms.CharField(max_length=32, required=False, label="Phone number")
    age = forms.IntegerField(required=False, min_value=0, max_value=130)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    allergy_status = forms.ChoiceField(choices=Patient.ALLERGY_STATUS, initial="unknown", label="Allergy status")
    allergies = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Allergies and reactions, if known"}))
    room_number = forms.CharField(max_length=40, required=False)
    admitted_on = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="Admission date")
    visit_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="Record date")
    temperature_c = forms.DecimalField(required=False, min_value=25, max_value=45, decimal_places=1, widget=forms.NumberInput(attrs={"step": "0.1"}))
    height_cm = forms.DecimalField(required=False, min_value=20, max_value=260, decimal_places=1, widget=forms.NumberInput(attrs={"step": "0.1"}))
    weight_kg = forms.DecimalField(required=False, min_value=0.5, max_value=500, decimal_places=1, widget=forms.NumberInput(attrs={"step": "0.1"}))
    other_symptoms = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Other symptoms"}))
    vomiting = forms.ChoiceField(choices=[("unknown", "Not recorded"), ("yes", "Yes"), ("no", "No")], initial="unknown")
    vomiting_days = forms.IntegerField(required=False, min_value=0, max_value=365)
    prescription_file = SecureUploadField(label="Prescription")
    xray_file = SecureUploadField(label="X-ray")
    xray_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="X-ray test date")
    blood_test_file = SecureUploadField(label="Blood test")
    blood_test_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Blood test date")
    ultrasound_file = SecureUploadField(label="Ultrasound")
    ultrasound_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Ultrasound test date")
    extra_scan_file = SecureUploadField(label="Extra scan")
    extra_scan_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Extra scan date")
    extra_test_file = SecureUploadField(label="Other test")
    extra_test_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Other test date")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("allergy_status") == "recorded" and not cleaned.get("allergies", "").strip():
            self.add_error("allergies", "Enter the allergy and reaction details, or choose another allergy status.")
        if cleaned.get("vomiting") == "yes" and cleaned.get("vomiting_days") is None:
            self.add_error("vomiting_days", "Enter how many days.")
        for file_field, (category, label) in FILE_FIELDS.items():
            if cleaned.get(file_field) and category != "prescription" and not cleaned.get(f"{category}_date"):
                self.add_error(f"{category}_date", f"Enter the {label.lower()} test date.")
        return cleaned


class VisitEntryForm(forms.Form):
    visit_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="Entry date")
    temperature_c = forms.DecimalField(required=False, min_value=25, max_value=45, decimal_places=1, widget=forms.NumberInput(attrs={"step": "0.1"}))
    height_cm = forms.DecimalField(required=False, min_value=20, max_value=260, decimal_places=1, widget=forms.NumberInput(attrs={"step": "0.1"}))
    weight_kg = forms.DecimalField(required=False, min_value=0.5, max_value=500, decimal_places=1, widget=forms.NumberInput(attrs={"step": "0.1"}))
    other_symptoms = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    vomiting = forms.ChoiceField(choices=[("unknown", "Not recorded"), ("yes", "Yes"), ("no", "No")], initial="unknown")
    vomiting_days = forms.IntegerField(required=False, min_value=0, max_value=365)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("vomiting") == "yes" and cleaned.get("vomiting_days") is None:
            self.add_error("vomiting_days", "Enter how many days.")
        return cleaned


class MedicineAdministrationForm(forms.Form):
    medicine_name = forms.CharField(max_length=200, label="Medicine given")
    administered_by_name = forms.CharField(max_length=160, label="Administered by")
    administered_at = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}), label="Date and time given")


class DoctorVisitLogForm(forms.Form):
    doctor_name = forms.CharField(max_length=160)
    visited_at = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}), label="Visit date and time")
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class DischargeDateForm(forms.Form):
    discharge_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="Discharge date")


class RecordDocumentsForm(forms.Form):
    prescription_file = SecureUploadField(label="Prescription")
    xray_file = SecureUploadField(label="X-ray")
    xray_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="X-ray test date")
    blood_test_file = SecureUploadField(label="Blood test")
    blood_test_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Blood test date")
    ultrasound_file = SecureUploadField(label="Ultrasound")
    ultrasound_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Ultrasound test date")
    extra_scan_file = SecureUploadField(label="Extra scan")
    extra_scan_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Extra scan date")
    extra_test_file = SecureUploadField(label="Other test")
    extra_test_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Other test date")

    def clean(self):
        cleaned = super().clean()
        for file_field, (category, label) in FILE_FIELDS.items():
            if cleaned.get(file_field) and category != "prescription" and not cleaned.get(f"{category}_date"):
                self.add_error(f"{category}_date", f"Enter the {label.lower()} test date.")
        return cleaned


class DoctorVisitForm(forms.Form):
    diagnosis = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    prescription = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    treatment_plan = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

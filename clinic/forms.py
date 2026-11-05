from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import VisitDocument

MAX_UPLOAD_BYTES = 15 * 1024 * 1024


class StaffVisitForm(forms.Form):
    visit_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    temperature_c = forms.DecimalField(required=False, min_value=25, max_value=45, decimal_places=1,
        widget=forms.NumberInput(attrs={"step": "0.1", "placeholder": "°C"}))
    next_recommended_visit = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    staff_notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Administrative or visit details"}))
    document_title = forms.CharField(max_length=160, required=False)
    document = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.png,.jpg,.jpeg"}))

    def clean_document(self):
        uploaded = self.cleaned_data.get("document")
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


class DoctorVisitForm(forms.Form):
    diagnosis = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    prescription = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    treatment_plan = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class PatientAndTaskForm(forms.Form):
    full_name = forms.CharField(max_length=160)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    phone = forms.CharField(max_length=32, required=False)
    visit_date = forms.DateField(initial=timezone.localdate, widget=forms.DateInput(attrs={"type": "date"}))
    assigned_to = forms.ModelChoiceField(queryset=get_user_model().objects.none(), label="Assign upload task to")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = get_user_model().objects.filter(groups__name="Staff", is_active=True).distinct().order_by("username")


class AssignVisitTaskForm(forms.Form):
    visit_date = forms.DateField(initial=timezone.localdate, widget=forms.DateInput(attrs={"type": "date"}))
    assigned_to = forms.ModelChoiceField(queryset=get_user_model().objects.none(), label="Assign upload task to")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = get_user_model().objects.filter(groups__name="Staff", is_active=True).distinct().order_by("username")

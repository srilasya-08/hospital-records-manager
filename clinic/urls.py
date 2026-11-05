from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("staff/patients/", views.staff_patient_list, name="staff_patient_list"),
    path("staff/patients/new/", views.staff_patient_create, name="staff_patient_create"),
    path("staff/patients/<uuid:public_id>/", views.staff_patient_detail, name="staff_patient_detail"),
    path("doctor/patients/", views.patient_list, name="patient_list"),
    path("doctor/patients/<uuid:public_id>/", views.patient_detail, name="patient_detail"),
    path("documents/<int:document_id>/", views.document_download, name="document_download"),
]

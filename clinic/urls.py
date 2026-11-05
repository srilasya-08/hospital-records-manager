from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("staff/tasks/", views.staff_tasks, name="staff_tasks"),
    path("staff/tasks/<uuid:task_code>/", views.staff_task, name="staff_task"),
    path("doctor/patients/", views.patient_list, name="patient_list"),
    path("doctor/patients/new/", views.patient_create, name="patient_create"),
    path("doctor/patients/<uuid:public_id>/", views.patient_detail, name="patient_detail"),
    path("doctor/patients/<uuid:public_id>/visits/new/", views.new_visit_task, name="new_visit_task"),
    path("doctor/documents/<int:document_id>/", views.document_download, name="document_download"),
]

from django.urls import path
from . import views

app_name = "pins"

urlpatterns = [
    path("pins/", views.pin_list, name="pin_list"),
    path("pins/submit/", views.submit_pin, name="submit_pin"),
    path("pins/pending/", views.pending_pins, name="pending_pins"),
    path("pins/<int:pin_id>/status/", views.set_pin_status, name="set_pin_status"),
    path("pins/seed/wikivoyage/", views.seed_wikivoyage_pins, name="seed_wikivoyage_pins"),
    path("my/pins/", views.my_pins, name="my_pins"),
    path("pins/<int:pin_id>/", views.pin_detail, name="pin_detail"),
    path("pins/<int:pin_id>/report/", views.report_pin, name="report_pin"),
    path("pins/reports/", views.list_pin_reports, name="list_pin_reports"),
    path("pins/reports/<int:report_id>/status/", views.set_pin_report_status, name="set_pin_report_status"),
]
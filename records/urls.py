from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DoctorViewSet, MappingDetailView, MappingListCreateView, PatientViewSet

router = DefaultRouter(trailing_slash=True)
router.register("patients", PatientViewSet, basename="patient")
router.register("doctors", DoctorViewSet, basename="doctor")

urlpatterns = router.urls + [
    path("mappings/", MappingListCreateView.as_view(), name="mapping-list"),
    path("mappings/<int:pk>/", MappingDetailView.as_view(), name="mapping-detail"),
]

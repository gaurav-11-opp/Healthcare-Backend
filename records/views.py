from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Doctor, Patient, PatientDoctorMapping
from .permissions import IsOwner, IsOwnerOrReadOnly
from .serializers import (
    AssignedDoctorSerializer,
    DoctorSerializer,
    MappingSerializer,
    PatientSerializer,
)


class PatientViewSet(viewsets.ModelViewSet):
    """CRUD for patients. Users only ever see and touch their own patients."""

    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Patient.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DoctorViewSet(viewsets.ModelViewSet):
    """Any authenticated user can read all doctors; only the creator can edit/delete."""

    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MappingListCreateView(generics.ListCreateAPIView):
    """POST assigns a doctor to one of your patients; GET lists mappings for your patients."""

    serializer_class = MappingSerializer

    def get_queryset(self):
        return PatientDoctorMapping.objects.filter(
            patient__created_by=self.request.user
        ).select_related("patient", "doctor")


class MappingDetailView(APIView):
    """
    GET    /api/mappings/<patient_id>/ -> doctors assigned to that patient
    DELETE /api/mappings/<id>/         -> remove that mapping
    """

    def get(self, request, pk):
        patient = get_object_or_404(Patient, pk=pk, created_by=request.user)
        mappings = patient.doctor_mappings.select_related("doctor")
        return Response(
            {
                "patient": {"id": patient.id, "name": patient.name},
                "doctors": AssignedDoctorSerializer(mappings, many=True).data,
            }
        )

    def delete(self, request, pk):
        mapping = get_object_or_404(
            PatientDoctorMapping, pk=pk, patient__created_by=request.user
        )
        mapping.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

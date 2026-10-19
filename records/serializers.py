from rest_framework import serializers

from .models import Doctor, Patient, PatientDoctorMapping


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = (
            "id", "name", "age", "gender", "phone", "address",
            "medical_history", "created_by", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = (
            "id", "name", "email", "phone", "specialization",
            "experience_years", "license_number", "created_by",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")

    def validate_email(self, value):
        return value.strip().lower()


class OwnedPatientField(serializers.PrimaryKeyRelatedField):
    """Only lets users reference patients they created (others look like 'does not exist')."""

    def get_queryset(self):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return Patient.objects.none()
        return Patient.objects.filter(created_by=request.user)


class MappingSerializer(serializers.ModelSerializer):
    patient = OwnedPatientField()
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True)
    doctor_specialization = serializers.CharField(source="doctor.specialization", read_only=True)

    class Meta:
        model = PatientDoctorMapping
        fields = (
            "id", "patient", "patient_name", "doctor", "doctor_name",
            "doctor_specialization", "assigned_at",
        )
        read_only_fields = ("id", "assigned_at")

    def validate(self, attrs):
        if PatientDoctorMapping.objects.filter(
            patient=attrs["patient"], doctor=attrs["doctor"]
        ).exists():
            raise serializers.ValidationError("This doctor is already assigned to this patient.")
        return attrs


class AssignedDoctorSerializer(serializers.ModelSerializer):
    """A mapping presented from the patient's side: mapping id + full doctor info."""

    mapping_id = serializers.IntegerField(source="id", read_only=True)
    doctor = DoctorSerializer(read_only=True)

    class Meta:
        model = PatientDoctorMapping
        fields = ("mapping_id", "assigned_at", "doctor")

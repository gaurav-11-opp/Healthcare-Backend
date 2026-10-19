from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()
PASSWORD = "Str0ng#Passw0rd"

PATIENT = {"name": "John Doe", "age": 40, "gender": "male", "phone": "+919876543210"}
DOCTOR = {
    "name": "Asha Rao", "email": "asha@example.com", "phone": "+919812345678",
    "specialization": "Cardiology", "experience_years": 10, "license_number": "LIC-001",
}


class AuthTests(APITestCase):
    def test_register_and_login(self):
        r = self.client.post("/api/auth/register/", {"name": "Al", "email": "Al@Example.com", "password": PASSWORD})
        self.assertEqual(r.status_code, 201)
        self.assertNotIn("password", r.data["user"])
        r = self.client.post("/api/auth/login/", {"email": "al@example.com", "password": PASSWORD})
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)
        self.assertIn("refresh", r.data)

    def test_duplicate_email_and_weak_password(self):
        User.objects.create_user(email="a@x.com", name="A", password=PASSWORD)
        r = self.client.post("/api/auth/register/", {"name": "B", "email": "A@x.com", "password": PASSWORD})
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/api/auth/register/", {"name": "B", "email": "b@x.com", "password": "12345678"})
        self.assertEqual(r.status_code, 400)

    def test_bad_login(self):
        r = self.client.post("/api/auth/login/", {"email": "no@x.com", "password": "nope"})
        self.assertEqual(r.status_code, 401)


class BaseAPITestCase(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user(email="alice@x.com", name="Alice", password=PASSWORD)
        self.bob = User.objects.create_user(email="bob@x.com", name="Bob", password=PASSWORD)

    def login(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class PatientTests(BaseAPITestCase):
    def test_requires_auth(self):
        self.assertEqual(self.client.get("/api/patients/").status_code, 401)

    def test_crud_and_isolation(self):
        self.login(self.alice)
        r = self.client.post("/api/patients/", PATIENT)
        self.assertEqual(r.status_code, 201)
        pid = r.data["id"]
        self.assertEqual(len(self.client.get("/api/patients/").data), 1)
        r = self.client.put(f"/api/patients/{pid}/", {**PATIENT, "age": 41})
        self.assertEqual(r.data["age"], 41)

        self.login(self.bob)
        self.assertEqual(len(self.client.get("/api/patients/").data), 0)
        self.assertEqual(self.client.get(f"/api/patients/{pid}/").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/patients/{pid}/").status_code, 404)

        self.login(self.alice)
        self.assertEqual(self.client.delete(f"/api/patients/{pid}/").status_code, 204)

    def test_validation(self):
        self.login(self.alice)
        r = self.client.post("/api/patients/", {**PATIENT, "age": 500, "phone": "abc"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("age", r.data["errors"])
        self.assertIn("phone", r.data["errors"])


class DoctorTests(BaseAPITestCase):
    def test_everyone_reads_only_owner_writes(self):
        self.login(self.alice)
        did = self.client.post("/api/doctors/", DOCTOR).data["id"]
        self.login(self.bob)
        self.assertEqual(len(self.client.get("/api/doctors/").data), 1)
        self.assertEqual(self.client.get(f"/api/doctors/{did}/").status_code, 200)
        self.assertEqual(self.client.put(f"/api/doctors/{did}/", DOCTOR).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/doctors/{did}/").status_code, 403)
        self.login(self.alice)
        self.assertEqual(self.client.delete(f"/api/doctors/{did}/").status_code, 204)

    def test_unique_email_and_license(self):
        self.login(self.alice)
        self.client.post("/api/doctors/", DOCTOR)
        r = self.client.post("/api/doctors/", DOCTOR)
        self.assertEqual(r.status_code, 400)


class MappingTests(BaseAPITestCase):
    def test_full_flow(self):
        self.login(self.alice)
        pid = self.client.post("/api/patients/", PATIENT).data["id"]
        did = self.client.post("/api/doctors/", DOCTOR).data["id"]

        r = self.client.post("/api/mappings/", {"patient": pid, "doctor": did})
        self.assertEqual(r.status_code, 201)
        mid = r.data["id"]

        self.assertEqual(self.client.post("/api/mappings/", {"patient": pid, "doctor": did}).status_code, 400)
        self.assertEqual(len(self.client.get("/api/mappings/").data), 1)

        r = self.client.get(f"/api/mappings/{pid}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["doctors"][0]["doctor"]["id"], did)

        self.assertEqual(self.client.delete(f"/api/mappings/{mid}/").status_code, 204)
        self.assertEqual(self.client.delete(f"/api/mappings/{mid}/").status_code, 404)

    def test_cannot_map_someone_elses_patient(self):
        self.login(self.alice)
        pid = self.client.post("/api/patients/", PATIENT).data["id"]
        did = self.client.post("/api/doctors/", DOCTOR).data["id"]
        self.login(self.bob)
        r = self.client.post("/api/mappings/", {"patient": pid, "doctor": did})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.client.get(f"/api/mappings/{pid}/").status_code, 404)

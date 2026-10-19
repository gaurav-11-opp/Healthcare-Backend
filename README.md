# Healthcare Backend (Django + DRF + PostgreSQL + JWT)

## Project structure
```
config/     settings, root urls, custom exception handler
accounts/   custom email-based User model, register/login endpoints
records/    Patient, Doctor, PatientDoctorMapping models, serializers, views, permissions, tests
```

## Setup
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# create the database
psql -U postgres -c "CREATE DATABASE healthcare_db;"

cp .env.example .env        # then edit SECRET_KEY and DB credentials
python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```
Run the tests: `python manage.py test`

## Endpoints
All endpoints except register/login require the header `Authorization: Bearer <access_token>`.

| Method | URL | Notes |
|---|---|---|
| POST | /api/auth/register/ | `name`, `email`, `password` |
| POST | /api/auth/login/ | `email`, `password` -> `access`, `refresh`, `user` |
| POST | /api/auth/token/refresh/ | `refresh` -> new `access` |
| POST/GET | /api/patients/ | GET returns only your patients |
| GET/PUT/DELETE | /api/patients/<id>/ | Owner only (others get 404) |
| POST/GET | /api/doctors/ | GET returns all doctors |
| GET | /api/doctors/<id>/ | Any authenticated user |
| PUT/DELETE | /api/doctors/<id>/ | Creator only (others get 403) |
| POST | /api/mappings/ | `patient`, `doctor` (patient must be yours) |
| GET | /api/mappings/ | Mappings for your patients |
| GET | /api/mappings/<patient_id>/ | Doctors assigned to that patient |
| DELETE | /api/mappings/<id>/ | `<id>` is the mapping id |

## Example requests
```bash
curl -X POST localhost:8000/api/auth/register/ -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","password":"Str0ng#Passw0rd"}'

curl -X POST localhost:8000/api/auth/login/ -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"Str0ng#Passw0rd"}'

curl -X POST localhost:8000/api/patients/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"John Doe","age":40,"gender":"male","phone":"+919876543210","address":"Delhi","medical_history":"Diabetes"}'

curl -X POST localhost:8000/api/doctors/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Asha Rao","email":"asha@example.com","phone":"+919812345678","specialization":"Cardiology","experience_years":10,"license_number":"LIC-001"}'

curl -X POST localhost:8000/api/mappings/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"patient":1,"doctor":1}'
```

## Error format
```json
{"status_code": 400, "errors": {"age": ["Ensure this value is less than or equal to 150."]}}
```

## Design notes
- Patients are private to the user who created them; mappings are likewise scoped to your own patients.
- Doctors are a shared directory: everyone can read, only the creator can modify/delete.
- Deleting a patient or doctor also deletes its mappings (cascade).
- Secrets and DB credentials come from `.env` (never commit it).

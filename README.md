# The Global Chronicle API

Standalone Django 5.2 and Django REST Framework 3.16 backend for The Global Chronicle.

## Local setup

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py runserver
```

The API runs at `http://127.0.0.1:8000/api/` by default. Put NewsAPI and GNews credentials only in the backend `.env` file; never commit it.

## Verification

```powershell
.\venv\Scripts\python.exe manage.py test core
.\venv\Scripts\python.exe manage.py check
```

## Deployment

`render.yaml` provisions the Django service and PostgreSQL database on Render. Set `FRONTEND_URL` to the deployed frontend origin.

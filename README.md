# Medical Lab Backend

This is the backend for the Medical Lab Database System, built using FastAPI and PostgreSQL.

## Features

- User authentication (Admin, Doctor, Lab Technician)
- Patient management
- Test request submission
- Test result uploads
- Equipment tracking
- Admin dashboards
- Email notifications and file attachments

## Technologies

- **FastAPI** (Python)
- **SQLAlchemy**
- **PostgreSQL** (via Supabase or external DB)
- **Render** (for deployment)

## Deployment

To deploy on Render:

1. Make sure `.env` contains:
    - `DATABASE_URL`
    - `SECRET_KEY`
    - `EMAIL_USER`
    - `EMAIL_PASSWORD`

2. Set `PYTHON_VERSION=3.12.10` as an environment variable or in `.python-version`.

3. Push to GitHub and deploy via Render.

---

This file is required by Poetry for deployment.

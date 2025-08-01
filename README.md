# 🧪 Medical Lab Backend

This is the backend service for the **Medical Lab Database System**, built using **FastAPI**, **SQLAlchemy**, and **PostgreSQL**. It provides API endpoints and business logic for managing users, patients, test requests, lab equipment, and test results.

---

## 🚀 Features

- 🔐 Role-based user authentication (Admin, Doctor, Lab Technician)
- 🧍‍♂️ Patient profile and record management
- 🧾 Test request submission by doctors
- 🧪 Test result upload by lab technicians (with file support)
- ⚙️ Equipment management and status tracking
- 📊 Admin dashboard and summaries
- 📧 Email notifications and file sharing

---

## 🧰 Technologies Used

- **FastAPI** – API framework
- **SQLAlchemy** – ORM
- **PostgreSQL** – Database (via Supabase or any PostgreSQL instance)
- **Pydantic** – Data validation
- **Streamlit** – Optional frontend interface
- **Render** – Cloud deployment

---

## 🛠️ Development Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/your-username/medical-lab-backend.git
cd medical-lab-backend
poetry install --no-root

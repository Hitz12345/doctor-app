# MediBook — Doctor Appointment Booking System

> A beginner-friendly university project demonstrating a full-stack web application for booking doctor appointments, built with **Python Flask**, **SQLite**, and vanilla **HTML/CSS/JavaScript**.

---

## 📋 Project Introduction

MediBook is a web-based Doctor Appointment Booking System that lets patients register, browse specialist doctors, and book appointments online. Administrators can manage the doctor roster and oversee all appointments through a dedicated dashboard.

---

## ❗ Problem Statement

Traditional appointment booking relies on phone calls or walk-ins, leading to scheduling conflicts, long wait times, and double bookings. MediBook provides a digital solution that is simple, accessible, and reliable.

---

## 🎯 Objectives

- Allow patients to register, log in, and book appointments online.
- Prevent double-booking of a doctor's time slot.
- Give administrators control over doctors and appointments.
- Demonstrate software engineering best practices (version control, testing, clean code).

---

## ✅ Functional Requirements

| ID  | Requirement |
|-----|-------------|
| FR1 | Patients can register and log in. |
| FR2 | Patients can view available doctors and their schedules. |
| FR3 | Patients can book an appointment on an available date and time. |
| FR4 | The system prevents booking in the past or on unavailable days. |
| FR5 | The system prevents two bookings at the same doctor–date–time. |
| FR6 | Patients can cancel their own appointments. |
| FR7 | Admins can add, edit, and delete doctors. |
| FR8 | Admins can approve or cancel any appointment. |
| FR9 | Patients can only view their own appointments. |

---

## ⚙️ Non-Functional Requirements

- **Security**: Passwords are hashed (bcrypt via Werkzeug). Pages are protected by role-based session checks.
- **Usability**: Clear success and error flash messages on every action.
- **Performance**: SQLite is sufficient for a university-scale project.
- **Maintainability**: Clean project structure; logic separated from templates.
- **Testability**: pytest suite covers all major features.

---

## 🛠️ Technologies

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, Flask 3 |
| Database | SQLite 3 |
| Frontend | HTML5, Vanilla CSS, Vanilla JavaScript |
| Auth | Flask sessions + Werkzeug password hashing |
| Testing | pytest |
| Version Control | Git + GitHub |

---

## 🏗️ System Features

### Patient
- Register / Login / Logout
- Browse all doctors with specialisation, available days, and time slots
- Book appointment (with live slot availability via AJAX)
- View own appointment list
- Cancel own appointments

### Admin
- Login / Logout
- Add / Edit / Delete doctors
- View all appointments across all patients
- Approve or cancel any appointment
- View summary statistics

---

## 🗄️ Database Design

### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| name | TEXT | Full name |
| email | TEXT UNIQUE | Used as login |
| password | TEXT | Hashed with Werkzeug |
| role | TEXT | `patient` or `admin` |

### `doctors`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| name | TEXT | Full name with "Dr." prefix |
| specialization | TEXT | e.g., Cardiologist |
| available_days | TEXT | Comma-separated day names |
| available_time | TEXT | Comma-separated HH:MM values |

### `appointments`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| patient_id | INTEGER FK | → users.id |
| doctor_id | INTEGER FK | → doctors.id |
| appointment_date | TEXT | YYYY-MM-DD |
| appointment_time | TEXT | HH:MM |
| status | TEXT | `pending`, `approved`, `cancelled` |
| created_at | TEXT | datetime('now') |

---

## 📁 Project Structure

```
doctor-appointment-system/
│
├── app.py                 # Flask application, routes, DB logic
├── database.db            # SQLite database (auto-created)
├── requirements.txt       # Python dependencies
├── README.md
├── .gitignore
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── doctors.html
│   ├── book_appointment.html
│   ├── appointments.html
│   └── admin.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
└── tests/
    └── test_app.py
```

---

## 🚀 How to Run

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/doctor-appointment-system.git
cd doctor-appointment-system
```

### 2. Create a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python app.py
```

Open your browser at **http://127.0.0.1:5000**

### Demo credentials
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@clinic.com | admin123 |
| Patient | Register a new account | — |

---

## 🧪 Testing

```bash
pytest tests/test_app.py -v
```

### Test coverage
| # | Test |
|---|------|
| 1 | Patient registration |
| 2 | Patient login |
| 3 | Invalid login (wrong password, unknown email) |
| 4 | Admin adds a doctor |
| 5 | Non-admin cannot add doctor |
| 6 | Booking a future appointment |
| 7 | Preventing double booking |
| 8 | Cancelling own appointment |
| 9 | Patient sees only own appointments |
| 10 | Admin can access dashboard |
| 11 | Admin can approve an appointment |
| 12 | Unauthenticated user redirected |
| 13 | Patient cannot access admin panel |
| 14 | Past-date booking rejected |

---

## 🔀 GitHub Workflow

### Branch strategy
| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code |
| `develop` | Integration branch |
| `feature/*` | Individual feature work |

### Feature branches used
- `feature/authentication`
- `feature/doctor-management`
- `feature/appointment-booking`
- `feature/double-booking-prevention`
- `feature/cancellation`
- `feature/admin-dashboard`
- `feature/testing`

---

## 📋 Change Management Process

Each change follows this workflow:

1. **Create a GitHub Issue** describing the change.
2. **Create a feature branch** from `develop`.
3. **Implement** the requested change.
4. **Write / run tests** to verify the change.
5. **Commit** with a meaningful commit message.
6. **Open a Pull Request** targeting `develop`.
7. **Review** the code (self-review or peer review).
8. **Merge** the PR into `develop`.
9. **Test** the integrated system on `develop`.
10. **Merge** `develop` into `main` when stable.

---

## 📌 Change Requests (GitHub Issues)

| Issue | Title | Branch |
|-------|-------|--------|
| #1 | Create patient registration and login | `feature/authentication` |
| #2 | Add doctor management | `feature/doctor-management` |
| #3 | Add appointment booking | `feature/appointment-booking` |
| #4 | Prevent double booking | `feature/double-booking-prevention` |
| #5 | Add appointment cancellation | `feature/cancellation` |
| #6 | Add admin dashboard | `feature/admin-dashboard` |
| #7 | Improve user interface | `feature/authentication` |
| #8 | Add automated testing | `feature/testing` |

---

## 🔮 Future Improvements

- Email notifications when an appointment is approved or cancelled.
- Patient profile page to edit personal details.
- Doctor-specific login to manage their own schedule.
- Calendar view for appointments.
- Pagination for large appointment lists.
- Export appointments to PDF or CSV.

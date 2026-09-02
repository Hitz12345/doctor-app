"""
Pytest test suite — Doctor Appointment Booking System
Run with: pytest tests/test_app.py -v
"""

import pytest
import sys
import os

# Make sure the app module is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app, init_db, get_db
from werkzeug.security import generate_password_hash


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a test client backed by a fresh in-memory-style database."""
    db_path = str(tmp_path / 'test.db')
    monkeypatch.setattr('app.DATABASE', db_path)
    app.config['TESTING']               = True
    app.config['WTF_CSRF_ENABLED']      = False
    app.config['SECRET_KEY']            = 'test-secret'

    with app.app_context():
        init_db()

    with app.test_client() as client:
        yield client


def register_patient(client, name='Test Patient', email='patient@test.com', password='pass123'):
    """Helper: register a patient account."""
    return client.post('/register', data=dict(
        name=name, email=email, password=password, confirm_password=password
    ), follow_redirects=True)


def login_user(client, email, password):
    """Helper: log in as any user."""
    return client.post('/login', data=dict(email=email, password=password),
                       follow_redirects=True)


def login_admin(client):
    return login_user(client, 'admin@clinic.com', 'admin123')


def add_doctor(client, name='Dr. Test', spec='Tester',
               days='Monday,Wednesday,Friday',
               times='09:00,10:00,14:00'):
    """Helper: add a doctor via admin panel."""
    login_admin(client)
    resp = client.post('/admin/doctor/add', data=dict(
        name=name,
        specialization=spec,
        available_days=days.split(','),
        available_time=times.split(',')
    ), follow_redirects=True)
    client.get('/logout')
    return resp


# ─────────────────────────────────────────────
# 1. Patient registration
# ─────────────────────────────────────────────

def test_patient_registration(client):
    """A new patient can register successfully."""
    resp = register_patient(client)
    assert resp.status_code == 200
    assert b'Registration successful' in resp.data or b'Sign in' in resp.data


def test_duplicate_registration(client):
    """Registering with the same email twice is rejected."""
    register_patient(client)
    resp = register_patient(client)
    assert b'already exists' in resp.data


def test_registration_password_mismatch(client):
    """Mismatched passwords are rejected on registration."""
    resp = client.post('/register', data=dict(
        name='Alice', email='alice@test.com',
        password='aaa111', confirm_password='bbb222'
    ), follow_redirects=True)
    assert b'do not match' in resp.data


# ─────────────────────────────────────────────
# 2. Patient login
# ─────────────────────────────────────────────

def test_patient_login(client):
    """A registered patient can log in."""
    register_patient(client)
    resp = login_user(client, 'patient@test.com', 'pass123')
    assert resp.status_code == 200
    assert b'Welcome back' in resp.data or b'Dashboard' in resp.data


# ─────────────────────────────────────────────
# 3. Invalid login
# ─────────────────────────────────────────────

def test_invalid_login_wrong_password(client):
    """Wrong password returns an error message."""
    register_patient(client)
    resp = login_user(client, 'patient@test.com', 'wrongpassword')
    assert b'Invalid email or password' in resp.data


def test_invalid_login_unknown_email(client):
    """Logging in with a non-existent email returns an error."""
    resp = login_user(client, 'nobody@test.com', 'anything')
    assert b'Invalid email or password' in resp.data


# ─────────────────────────────────────────────
# 4. Adding a doctor (admin)
# ─────────────────────────────────────────────

def test_admin_add_doctor(client):
    """Admin can add a new doctor."""
    login_admin(client)
    resp = client.post('/admin/doctor/add', data=dict(
        name='Dr. Newdoc',
        specialization='Dentist',
        available_days=['Monday', 'Friday'],
        available_time=['09:00', '10:00']
    ), follow_redirects=True)
    assert b'Doctor added successfully' in resp.data


def test_non_admin_cannot_add_doctor(client):
    """A patient cannot add a doctor."""
    register_patient(client)
    login_user(client, 'patient@test.com', 'pass123')
    resp = client.post('/admin/doctor/add', data=dict(
        name='Hack', specialization='None',
        available_days=['Monday'], available_time=['09:00']
    ), follow_redirects=True)
    assert resp.status_code == 200
    # either redirected or denied
    assert b'Doctor added' not in resp.data


# ─────────────────────────────────────────────
# 5. Booking an appointment
# ─────────────────────────────────────────────

def test_book_appointment(client):
    """A patient can book an available slot for a future date."""
    add_doctor(client)

    register_patient(client)
    login_user(client, 'patient@test.com', 'pass123')

    # get doctor id
    with client.application.app_context():
        from app import get_db, DATABASE
        import app as app_module
        import sqlite3
        conn = sqlite3.connect(app_module.DATABASE)
        conn.row_factory = sqlite3.Row
        doc = conn.execute("SELECT id FROM doctors WHERE name = 'Dr. Test'").fetchone()
        conn.close()
        doc_id = doc['id']

    resp = client.post(f'/book/{doc_id}', data=dict(
        appointment_date='2027-01-06',   # a future Monday
        appointment_time='09:00'
    ), follow_redirects=True)
    assert b'booked successfully' in resp.data


# ─────────────────────────────────────────────
# 6. Preventing double booking
# ─────────────────────────────────────────────

def test_prevent_double_booking(client):
    """Two patients cannot book the same doctor slot on the same day/time."""
    add_doctor(client)

    # Patient 1
    register_patient(client, name='P1', email='p1@test.com')
    login_user(client, 'p1@test.com', 'pass123')

    import sqlite3, app as app_module
    conn = sqlite3.connect(app_module.DATABASE)
    conn.row_factory = sqlite3.Row
    doc = conn.execute("SELECT id FROM doctors WHERE name = 'Dr. Test'").fetchone()
    conn.close()
    doc_id = doc['id']

    client.post(f'/book/{doc_id}', data=dict(
        appointment_date='2027-01-06',
        appointment_time='09:00'
    ), follow_redirects=True)
    client.get('/logout', follow_redirects=True)

    # Patient 2 tries same slot
    register_patient(client, name='P2', email='p2@test.com')
    login_user(client, 'p2@test.com', 'pass123')
    resp = client.post(f'/book/{doc_id}', data=dict(
        appointment_date='2027-01-06',
        appointment_time='09:00'
    ), follow_redirects=True)
    assert b'already booked' in resp.data


# ─────────────────────────────────────────────
# 7. Cancelling an appointment
# ─────────────────────────────────────────────

def test_cancel_appointment(client):
    """A patient can cancel their own appointment."""
    add_doctor(client)

    register_patient(client)
    login_user(client, 'patient@test.com', 'pass123')

    import sqlite3, app as app_module
    conn = sqlite3.connect(app_module.DATABASE)
    conn.row_factory = sqlite3.Row
    doc = conn.execute("SELECT id FROM doctors WHERE name = 'Dr. Test'").fetchone()
    conn.close()
    doc_id = doc['id']

    client.post(f'/book/{doc_id}', data=dict(
        appointment_date='2027-01-06',
        appointment_time='10:00'
    ), follow_redirects=True)

    # find the appointment id
    conn = sqlite3.connect(app_module.DATABASE)
    conn.row_factory = sqlite3.Row
    appt = conn.execute("SELECT id FROM appointments WHERE appointment_time='10:00'").fetchone()
    conn.close()

    resp = client.post(f'/cancel/{appt["id"]}', follow_redirects=True)
    assert b'cancelled successfully' in resp.data


# ─────────────────────────────────────────────
# 8. Patient can only see own appointments
# ─────────────────────────────────────────────

def test_patient_sees_only_own_appointments(client):
    """Patient A cannot see patient B's appointments on their dashboard."""
    add_doctor(client)

    register_patient(client, name='Alice', email='alice@test.com', password='alice123')
    register_patient(client, name='Bob',   email='bob@test.com',   password='bob123')

    import sqlite3, app as app_module
    conn = sqlite3.connect(app_module.DATABASE)
    conn.row_factory = sqlite3.Row
    doc = conn.execute("SELECT id FROM doctors WHERE name = 'Dr. Test'").fetchone()
    conn.close()
    doc_id = doc['id']

    # Alice books
    login_user(client, 'alice@test.com', 'alice123')
    client.post(f'/book/{doc_id}', data=dict(
        appointment_date='2027-01-06', appointment_time='09:00'
    ), follow_redirects=True)
    client.get('/logout', follow_redirects=True)

    # Bob logs in and checks his appointments — Alice's should NOT appear
    login_user(client, 'bob@test.com', 'bob123')
    resp = client.get('/appointments')
    # Bob booked nothing
    assert b'alice' not in resp.data.lower()


# ─────────────────────────────────────────────
# 9. Admin access control
# ─────────────────────────────────────────────

def test_admin_can_access_dashboard(client):
    """Admin reaches the admin dashboard."""
    login_admin(client)
    resp = client.get('/admin', follow_redirects=True)
    assert resp.status_code == 200
    assert b'Admin Dashboard' in resp.data or b'Doctor Management' in resp.data


def test_admin_can_approve_appointment(client):
    """Admin can approve a pending appointment."""
    add_doctor(client)

    register_patient(client)
    login_user(client, 'patient@test.com', 'pass123')

    import sqlite3, app as app_module
    conn = sqlite3.connect(app_module.DATABASE)
    conn.row_factory = sqlite3.Row
    doc = conn.execute("SELECT id FROM doctors WHERE name = 'Dr. Test'").fetchone()
    conn.close()
    doc_id = doc['id']

    client.post(f'/book/{doc_id}', data=dict(
        appointment_date='2027-01-06', appointment_time='09:00'
    ), follow_redirects=True)
    client.get('/logout', follow_redirects=True)

    login_admin(client)
    conn = sqlite3.connect(app_module.DATABASE)
    conn.row_factory = sqlite3.Row
    appt = conn.execute("SELECT id FROM appointments").fetchone()
    conn.close()

    resp = client.post(f'/admin/appointment/approve/{appt["id"]}', follow_redirects=True)
    assert b'approved' in resp.data


# ─────────────────────────────────────────────
# 10. Unauthorized access protection
# ─────────────────────────────────────────────

def test_unauthenticated_cannot_access_dashboard(client):
    """Unauthenticated users are redirected from the dashboard."""
    resp = client.get('/dashboard', follow_redirects=True)
    assert b'Sign in' in resp.data or b'log in' in resp.data.lower()


def test_unauthenticated_cannot_access_admin(client):
    """Unauthenticated users cannot reach the admin panel."""
    resp = client.get('/admin', follow_redirects=True)
    assert b'Admin Dashboard' not in resp.data


def test_patient_cannot_access_admin(client):
    """A logged-in patient cannot see the admin dashboard."""
    register_patient(client)
    login_user(client, 'patient@test.com', 'pass123')
    resp = client.get('/admin', follow_redirects=True)
    assert b'Doctor Management' not in resp.data


def test_past_date_booking_rejected(client):
    """Booking a date in the past must be rejected."""
    add_doctor(client)

    register_patient(client)
    login_user(client, 'patient@test.com', 'pass123')

    import sqlite3, app as app_module
    conn = sqlite3.connect(app_module.DATABASE)
    conn.row_factory = sqlite3.Row
    doc = conn.execute("SELECT id FROM doctors WHERE name = 'Dr. Test'").fetchone()
    conn.close()
    doc_id = doc['id']

    resp = client.post(f'/book/{doc_id}', data=dict(
        appointment_date='2020-01-01',
        appointment_time='09:00'
    ), follow_redirects=True)
    assert b'past' in resp.data or b'cannot book' in resp.data.lower()

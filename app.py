from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.secret_key = 'doctor_appointment_secret_key_2024'

DATABASE = 'database.db'


# ─────────────────────────────────────────────
# Database helpers
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT    NOT NULL,
                email    TEXT    NOT NULL UNIQUE,
                password TEXT    NOT NULL,
                role     TEXT    NOT NULL DEFAULT 'patient'
            );

            CREATE TABLE IF NOT EXISTS doctors (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL,
                specialization  TEXT NOT NULL,
                available_days  TEXT NOT NULL,
                available_time  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS appointments (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id       INTEGER NOT NULL,
                doctor_id        INTEGER NOT NULL,
                appointment_date TEXT    NOT NULL,
                appointment_time TEXT    NOT NULL,
                status           TEXT    NOT NULL DEFAULT 'pending',
                created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (patient_id) REFERENCES users(id),
                FOREIGN KEY (doctor_id)  REFERENCES doctors(id)
            );
        ''')

        # seed admin account if not present
        admin = conn.execute("SELECT id FROM users WHERE email = 'admin@clinic.com'").fetchone()
        if not admin:
            conn.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                ('Admin', 'admin@clinic.com', generate_password_hash('admin123'), 'admin')
            )

        # seed sample doctors if none exist
        count = conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
        if count == 0:
            sample_doctors = [
               ('Dr. Mya Mya',      'General Physician',  'Monday,Wednesday,Friday',    '09:00,10:00,11:00,14:00,15:00'),
                ('Dr. Aung Kyaw',    'Dentist',            'Tuesday,Thursday,Saturday',  '09:00,10:00,11:00,14:00,15:00'),
                ('Dr. Khin Khin',    'Pediatrician',       'Monday,Tuesday,Wednesday',   '10:00,11:00,14:00,15:00,16:00'),
                ('Dr. Zaw Lin',      'Orthopedist',        'Wednesday,Thursday,Friday',  '09:00,10:00,14:00,15:00,16:00'),
                ('Dr. Su Su',        'Dermatologist',      'Monday,Thursday,Friday',     '09:00,10:00,11:00,14:00,15:00'),
                ('Dr. Htet Htet',    'Eye Specialist',     'Tuesday,Wednesday,Saturday', '09:00,10:00,14:00,15:00,16:00'),
                ('Dr. Nay Lin',      'ENT Specialist',     'Monday,Friday,Saturday',     '10:00,11:00,14:00,15:00,16:00'),
            ]
            conn.executemany(
                "INSERT INTO doctors (name, specialization, available_days, available_time) VALUES (?, ?, ?, ?)",
                sample_doctors
            )
        conn.commit()


# ─────────────────────────────────────────────
# Decorators
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def patient_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'patient':
            flash('Access denied.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
# General routes
# ─────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('dashboard'))


# ─────────────────────────────────────────────
# Auth routes
# ─────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')

        with get_db() as conn:
            existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing:
                flash('An account with this email already exists.', 'danger')
                return render_template('register.html')
            conn.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, 'patient')",
                (name, email, generate_password_hash(password))
            )
            conn.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('login.html')

        with get_db() as conn:
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['name']    = user['name']
            session['role']    = user['role']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ─────────────────────────────────────────────
# Patient routes
# ─────────────────────────────────────────────

@app.route('/dashboard')
@patient_required
def dashboard():
    with get_db() as conn:
        appointments = conn.execute(
            '''SELECT a.*, d.name AS doctor_name, d.specialization
               FROM appointments a
               JOIN doctors d ON a.doctor_id = d.id
               WHERE a.patient_id = ?
               ORDER BY a.appointment_date DESC, a.appointment_time DESC''',
            (session['user_id'],)
        ).fetchall()
    return render_template('dashboard.html', appointments=appointments)


@app.route('/doctors')
@patient_required
def doctors():
    with get_db() as conn:
        doctors_list = conn.execute("SELECT * FROM doctors ORDER BY name").fetchall()
    return render_template('doctors.html', doctors=doctors_list)


@app.route('/book/<int:doctor_id>', methods=['GET', 'POST'])
@patient_required
def book_appointment(doctor_id):
    with get_db() as conn:
        doctor = conn.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,)).fetchone()

    if not doctor:
        flash('Doctor not found.', 'danger')
        return redirect(url_for('doctors'))

    if request.method == 'POST':
        appt_date = request.form.get('appointment_date', '').strip()
        appt_time = request.form.get('appointment_time', '').strip()

        # validation
        if not appt_date or not appt_time:
            flash('Please select both a date and a time.', 'danger')
            return render_template('book_appointment.html', doctor=doctor)

        try:
            selected_date = datetime.strptime(appt_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return render_template('book_appointment.html', doctor=doctor)

        if selected_date < date.today():
            flash('You cannot book an appointment in the past.', 'danger')
            return render_template('book_appointment.html', doctor=doctor)

        # check day availability
        day_name = selected_date.strftime('%A')
        available_days = [d.strip() for d in doctor['available_days'].split(',')]
        if day_name not in available_days:
            flash(f'Dr. {doctor["name"]} is not available on {day_name}.', 'danger')
            return render_template('book_appointment.html', doctor=doctor)

        # check time availability
        available_times = [t.strip() for t in doctor['available_time'].split(',')]
        if appt_time not in available_times:
            flash('Selected time is not available.', 'danger')
            return render_template('book_appointment.html', doctor=doctor)

        with get_db() as conn:
            # double-booking prevention
            conflict = conn.execute(
                '''SELECT id FROM appointments
                   WHERE doctor_id = ? AND appointment_date = ? AND appointment_time = ?
                   AND status != 'cancelled' ''',
                (doctor_id, appt_date, appt_time)
            ).fetchone()

            if conflict:
                flash('This time slot is already booked. Please choose a different time.', 'danger')
                return render_template('book_appointment.html', doctor=doctor)

            conn.execute(
                '''INSERT INTO appointments
                   (patient_id, doctor_id, appointment_date, appointment_time, status, created_at)
                   VALUES (?, ?, ?, ?, 'pending', datetime('now'))''',
                (session['user_id'], doctor_id, appt_date, appt_time)
            )
            conn.commit()

        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('my_appointments'))

    return render_template('book_appointment.html', doctor=doctor)


@app.route('/appointments')
@patient_required
def my_appointments():
    with get_db() as conn:
        appointments = conn.execute(
            '''SELECT a.*, d.name AS doctor_name, d.specialization
               FROM appointments a
               JOIN doctors d ON a.doctor_id = d.id
               WHERE a.patient_id = ?
               ORDER BY a.appointment_date DESC, a.appointment_time DESC''',
            (session['user_id'],)
        ).fetchall()
    return render_template('appointments.html', appointments=appointments)


@app.route('/cancel/<int:appt_id>', methods=['POST'])
@patient_required
def cancel_appointment(appt_id):
    with get_db() as conn:
        # make sure the appointment belongs to the logged-in patient
        appt = conn.execute(
            "SELECT id FROM appointments WHERE id = ? AND patient_id = ?",
            (appt_id, session['user_id'])
        ).fetchone()

        if not appt:
            flash('Appointment not found or access denied.', 'danger')
            return redirect(url_for('my_appointments'))

        conn.execute(
            "UPDATE appointments SET status = 'cancelled' WHERE id = ?",
            (appt_id,)
        )
        conn.commit()

    flash('Appointment cancelled successfully.', 'success')
    return redirect(url_for('my_appointments'))


# ─────────────────────────────────────────────
# API – get booked slots (AJAX)
# ─────────────────────────────────────────────

@app.route('/api/booked_slots/<int:doctor_id>/<appt_date>')
@login_required
def booked_slots(doctor_id, appt_date):
    with get_db() as conn:
        rows = conn.execute(
            '''SELECT appointment_time FROM appointments
               WHERE doctor_id = ? AND appointment_date = ? AND status != 'cancelled' ''',
            (doctor_id, appt_date)
        ).fetchall()
    return jsonify([r['appointment_time'] for r in rows])


# ─────────────────────────────────────────────
# Admin routes
# ─────────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin_dashboard():
    with get_db() as conn:
        doctors_list  = conn.execute("SELECT * FROM doctors ORDER BY name").fetchall()
        appointments  = conn.execute(
            '''SELECT a.*, u.name AS patient_name, u.email AS patient_email,
                      d.name AS doctor_name, d.specialization
               FROM appointments a
               JOIN users    u ON a.patient_id = u.id
               JOIN doctors  d ON a.doctor_id  = d.id
               ORDER BY a.appointment_date DESC, a.appointment_time DESC'''
        ).fetchall()
        total_patients = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'patient'"
        ).fetchone()[0]
    return render_template('admin.html',
                           doctors=doctors_list,
                           appointments=appointments,
                           total_patients=total_patients)


@app.route('/admin/doctor/add', methods=['POST'])
@admin_required
def admin_add_doctor():
    name           = request.form.get('name', '').strip()
    specialization = request.form.get('specialization', '').strip()
    available_days = request.form.getlist('available_days')
    available_time = request.form.getlist('available_time')

    if not name or not specialization or not available_days or not available_time:
        flash('All fields are required.', 'danger')
        return redirect(url_for('admin_dashboard'))

    with get_db() as conn:
        conn.execute(
            "INSERT INTO doctors (name, specialization, available_days, available_time) VALUES (?, ?, ?, ?)",
            (name, specialization, ','.join(available_days), ','.join(available_time))
        )
        conn.commit()

    flash('Doctor added successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/doctor/edit/<int:doctor_id>', methods=['POST'])
@admin_required
def admin_edit_doctor(doctor_id):
    name           = request.form.get('name', '').strip()
    specialization = request.form.get('specialization', '').strip()
    available_days = request.form.getlist('available_days')
    available_time = request.form.getlist('available_time')

    if not name or not specialization or not available_days or not available_time:
        flash('All fields are required.', 'danger')
        return redirect(url_for('admin_dashboard'))

    with get_db() as conn:
        conn.execute(
            '''UPDATE doctors SET name=?, specialization=?, available_days=?, available_time=?
               WHERE id=?''',
            (name, specialization, ','.join(available_days), ','.join(available_time), doctor_id)
        )
        conn.commit()

    flash('Doctor updated successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/doctor/delete/<int:doctor_id>', methods=['POST'])
@admin_required
def admin_delete_doctor(doctor_id):
    with get_db() as conn:
        conn.execute("DELETE FROM doctors WHERE id = ?", (doctor_id,))
        conn.commit()

    flash('Doctor deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/appointment/approve/<int:appt_id>', methods=['POST'])
@admin_required
def admin_approve_appointment(appt_id):
    with get_db() as conn:
        conn.execute(
            "UPDATE appointments SET status = 'approved' WHERE id = ?",
            (appt_id,)
        )
        conn.commit()

    flash('Appointment approved.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/appointment/cancel/<int:appt_id>', methods=['POST'])
@admin_required
def admin_cancel_appointment(appt_id):
    with get_db() as conn:
        conn.execute(
            "UPDATE appointments SET status = 'cancelled' WHERE id = ?",
            (appt_id,)
        )
        conn.commit()

    flash('Appointment cancelled.', 'success')
    return redirect(url_for('admin_dashboard'))


# ─────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

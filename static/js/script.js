/* ─── Doctor Appointment Booking System — Main JavaScript ─── */

document.addEventListener('DOMContentLoaded', () => {

    /* ── Auto-dismiss flash messages ── */
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 500);
        }, 4000);
    });

    /* ── Tab switching ── */
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const group = btn.closest('[data-tabs]') || btn.parentElement.parentElement;
            const target = btn.dataset.tab;

            // deactivate all tabs in the same group
            btn.parentElement.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            group.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            const panel = group.querySelector(`#${target}`);
            if (panel) panel.classList.add('active');
        });
    });

    /* ── Modal helpers ── */
    window.openModal = (id) => {
        const modal = document.getElementById(id);
        if (modal) modal.classList.add('open');
    };

    window.closeModal = (id) => {
        const modal = document.getElementById(id);
        if (modal) modal.classList.remove('open');
    };

    // Close on backdrop click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.classList.remove('open');
        });
    });

    // Esc key closes modals
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
        }
    });

    /* ── Check-item toggle (visual feedback for checkboxes) ── */
    document.querySelectorAll('.check-item').forEach(item => {
        const cb = item.querySelector('input[type="checkbox"]');
        if (cb) {
            const update = () => item.classList.toggle('checked', cb.checked);
            update();
            cb.addEventListener('change', update);
        }
    });

    /* ── Time-slot picker ── */
    const slotContainer = document.getElementById('time-slots-container');
    const hiddenTimeInput = document.getElementById('appointment_time');
    const dateInput = document.getElementById('appointment_date_input');

    if (slotContainer && dateInput) {
        const doctorId = slotContainer.dataset.doctorId;

        const renderSlots = async () => {
            const dateVal = dateInput.value;
            if (!dateVal) return;

            // Determine day name
            const [y, m, d] = dateVal.split('-').map(Number);
            const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const dayName = dayNames[new Date(y, m - 1, d).getDay()];

            // Available times from data attribute (comma-separated)
            const allTimes = (slotContainer.dataset.times || '').split(',').map(t => t.trim()).filter(Boolean);
            const availableDays = (slotContainer.dataset.days || '').split(',').map(d => d.trim());

            // Fetch already booked slots
            let booked = [];
            if (doctorId && dateVal) {
                try {
                    const res = await fetch(`/api/booked_slots/${doctorId}/${dateVal}`);
                    booked = await res.json();
                } catch (_) { /* ignore */ }
            }

            slotContainer.innerHTML = '';

            if (!availableDays.includes(dayName)) {
                slotContainer.innerHTML = `<p class="text-muted small" style="grid-column:1/-1">
          Doctor not available on <strong>${dayName}</strong>. Please choose another date.</p>`;
                return;
            }

            if (allTimes.length === 0) {
                slotContainer.innerHTML = `<p class="text-muted small" style="grid-column:1/-1">No time slots configured.</p>`;
                return;
            }

            allTimes.forEach(time => {
                const isBooked = booked.includes(time);
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'time-slot' + (isBooked ? ' booked' : '');
                btn.textContent = time;
                btn.title = isBooked ? 'Already booked' : time;
                btn.disabled = isBooked;

                btn.addEventListener('click', () => {
                    if (isBooked) return;
                    slotContainer.querySelectorAll('.time-slot').forEach(s => s.classList.remove('selected'));
                    btn.classList.add('selected');
                    hiddenTimeInput.value = time;
                });

                slotContainer.appendChild(btn);
            });
        };

        dateInput.addEventListener('change', () => {
            if (hiddenTimeInput) hiddenTimeInput.value = '';
            slotContainer.querySelectorAll('.time-slot').forEach(s => s.classList.remove('selected'));
            renderSlots();
        });

        // Initialize if date is pre-filled
        if (dateInput.value) renderSlots();
    }

    /* ── Enforce min date = today on date inputs ── */
    const today = new Date().toISOString().split('T')[0];
    document.querySelectorAll('input[type="date"].future-only').forEach(inp => {
        inp.min = today;
    });

    /* ── Edit-doctor modal pre-fill ── */
    document.querySelectorAll('[data-edit-doctor]').forEach(btn => {
        btn.addEventListener('click', () => {
            const data = JSON.parse(btn.dataset.editDoctor);
            const modal = document.getElementById('editDoctorModal');
            if (!modal) return;

            modal.querySelector('[name="name"]').value = data.name;
            modal.querySelector('[name="specialization"]').value = data.specialization;
            modal.querySelector('form').action = `/admin/doctor/edit/${data.id}`;

            const days = data.available_days.split(',');
            const times = data.available_time.split(',');

            modal.querySelectorAll('input[name="available_days"]').forEach(cb => {
                cb.checked = days.includes(cb.value);
                const item = cb.closest('.check-item');
                if (item) item.classList.toggle('checked', cb.checked);
            });

            modal.querySelectorAll('input[name="available_time"]').forEach(cb => {
                cb.checked = times.includes(cb.value);
                const item = cb.closest('.check-item');
                if (item) item.classList.toggle('checked', cb.checked);
            });

            openModal('editDoctorModal');
        });
    });

    /* ── Confirm before destructive actions ── */
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', (e) => {
            const msg = el.dataset.confirm || 'Are you sure?';
            if (!confirm(msg)) e.preventDefault();
        });
    });

});

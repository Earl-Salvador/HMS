// Hotel Management System - JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing confirmations...');

    // 1. Handle logout link
    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(e) {
            e.preventDefault();
            Swal.fire({
                title: 'Logout?',
                text: 'Are you sure you want to logout?',
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Yes, logout',
                cancelButtonText: 'Cancel'
            }).then((result) => {
                if (result.isConfirmed) {
                    document.getElementById('logout-form').submit();
                }
            });
        });
    }

    // 2. Handle forms with data-confirm attribute (delegated)
    document.body.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.hasAttribute('data-confirm')) {
            e.preventDefault();
            const confirmMsg = form.getAttribute('data-confirm');
            Swal.fire({
                title: 'Confirm',
                text: confirmMsg,
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Yes, proceed',
                cancelButtonText: 'Cancel'
            }).then((result) => {
                if (result.isConfirmed) {
                    form.submit();
                }
            });
        }
    });

    // 3. Booking form
    const bookingForm = document.getElementById('booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const roomSelect = document.getElementById('room_id');
            const roomText = roomSelect.options[roomSelect.selectedIndex]?.text;
            const checkIn = document.getElementById('check_in').value;
            const checkOut = document.getElementById('check_out').value;
            const coupon = document.getElementById('coupon')?.value;
            Swal.fire({
                title: 'Confirm Booking',
                html: `<p><strong>Room:</strong> ${roomText}</p>
                       <p><strong>Check-in:</strong> ${checkIn}</p>
                       <p><strong>Check-out:</strong> ${checkOut}</p>
                       ${coupon ? `<p><strong>Coupon:</strong> ${coupon}</p>` : ''}
                       <p>Proceed with this booking?</p>`,
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Confirm Booking',
                cancelButtonText: 'Cancel'
            }).then((result) => {
                if (result.isConfirmed) {
                    bookingForm.submit();
                }
            });
        });
    }

    // 4. Payment form
    const paymentForm = document.getElementById('payment-form');
    if (paymentForm) {
        paymentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const totalSpan = document.getElementById('total-amount');
            const totalAmount = totalSpan ? totalSpan.innerText : 'unknown';
            Swal.fire({
                title: 'Confirm Payment',
                html: `<p>You are about to pay <strong>${totalAmount}</strong>.</p><p>Proceed?</p>`,
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Pay Now',
                cancelButtonText: 'Cancel'
            }).then((result) => {
                if (result.isConfirmed) {
                    paymentForm.submit();
                }
            });
        });
    }

    // Optional: Auto-hide flash messages after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

document.getElementById('register-form').addEventListener('submit', function(e) {
    console.log('Form submitted'); // Add this line to debug
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirm = document.getElementById('confirm_password').value;
    const phone = document.getElementById('phone').value.trim();
    
    const nameRegex = /^[A-Za-z\s'-]{2,50}$/;
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    const phoneRegex = /^\d{11}$/;

    let errors = [];
    if (!nameRegex.test(name)) errors.push("Name must be 2-50 letters, spaces, hyphens, apostrophes.");
    if (!emailRegex.test(email)) errors.push("Invalid email format.");
    if (!passwordRegex.test(password)) errors.push("Password must be at least 8 chars with uppercase, lowercase, number.");
    if (password !== confirm) errors.push("Passwords do not match.");
    if (!phoneRegex.test(phone)) errors.push("Phone must be exactly 11 digits.");

    if (errors.length > 0) {
        e.preventDefault();
        Swal.fire({
            icon: 'error',
            title: 'Validation Error',
            html: errors.join('<br>'),
            confirmButtonColor: '#92B775'
        });
    } else {
        console.log('Validation passed, submitting...');
    }
});

src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.9/index.global.min.js'


document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: '{{ url_for("bookings.calendar_data") }}',
        eventClick: function(info) {
            // Optional: show details or link to booking
            if (info.event.url) {
                window.open(info.event.url);
                info.jsEvent.preventDefault();
            }
        },
        eventDidMount: function(info) {
            // Add tooltip on hover
            info.el.setAttribute('title', info.event.title);
        },
        height: 'auto',
        weekends: true,
        nowIndicator: true,
        locale: 'en'
    });
    calendar.render();
});

function validateFirstName() {
    const name = document.getElementById('first_name').value.trim();
    const feedback = document.getElementById('first_name-feedback');
    if (!name) {
        feedback.textContent = 'First name is required.';
        return false;
    }
    if (!nameRegex.test(name)) {
        feedback.textContent = 'Only letters, spaces, hyphens, apostrophes (2-50 chars).';
        return false;
    }
    feedback.textContent = '';
    return true;
}

function validateLastName() {
    const name = document.getElementById('last_name').value.trim();
    const feedback = document.getElementById('last_name-feedback');
    if (!name) {
        feedback.textContent = 'Last name is required.';
        return false;
    }
    if (!nameRegex.test(name)) {
        feedback.textContent = 'Only letters, spaces, hyphens, apostrophes (2-50 chars).';
        return false;
    }
    feedback.textContent = '';
    return true;
}

document.getElementById('register-form').addEventListener('submit', function(e) {
    let isValid = true;
    if (!validateFirstName()) isValid = false;
    if (!validateLastName()) isValid = false;
    // ... other validations
    if (!isValid) {
        e.preventDefault();
        // show error
    }
});
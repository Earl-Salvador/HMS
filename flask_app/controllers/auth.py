from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, EmailVerification, PasswordReset
from werkzeug.security import generate_password_hash, check_password_hash
from utils.validators import validate_name, validate_email, validate_password
from utils.email_utils import send_verification_email, send_password_reset_email
from datetime import datetime, timedelta
import re
import secrets

bp = Blueprint('auth', __name__)

# -------------------- VALIDATION HELPERS --------------------
def validate_name(name):
    return bool(re.match(r"^[A-Za-z\s'-]{2,50}$", name))

def validate_email(email):
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))

def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True

def has_consecutive_digits(number, max_repeat=3):
    """Check if the number contains more than max_repeat identical digits in a row."""
    digits = ''.join(filter(str.isdigit, number))
    for i in range(len(digits) - max_repeat):
        if len(set(digits[i:i+max_repeat+1])) == 1:
            return True
    return False

# -------------------- LOGIN --------------------
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            if user.is_blocked:
                flash('Your account has been blocked. Please contact support.', 'danger')
                return redirect(url_for('auth.login'))
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('dashboard.admin_dashboard'))
            elif user.role == 'staff':
                return redirect(url_for('dashboard.staff_dashboard'))
            else:
                return redirect(url_for('dashboard.guest_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

# -------------------- REGISTRATION --------------------
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        full_name = f"{first_name} {last_name}".strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        raw_phone = request.form.get('phone', '').strip()

        errors = []

        # Name validation
        if not validate_name(first_name):
            errors.append("First name must be 2-50 letters, spaces, hyphens, apostrophes.")
        if not validate_name(last_name):
            errors.append("Last name must be 2-50 letters, spaces, hyphens, apostrophes.")
        if not validate_email(email):
            errors.append("Invalid email format.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")
        if not validate_password(password):
            errors.append("Password must be at least 8 characters with one uppercase, one lowercase, and one number.")
        if password != confirm:
            errors.append("Passwords do not match.")

        # Phone number validation (Philippines only)
        if not raw_phone.isdigit() or len(raw_phone) != 10:
            errors.append("Phone must be exactly 10 digits.")
        else:
            full_phone = f"+63{raw_phone}"
            if has_consecutive_digits(raw_phone):
                errors.append("Phone number cannot contain more than three identical digits in a row.")
            if User.query.filter_by(phone=full_phone).first():
                errors.append("Phone number already registered.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('register.html',
                                   first_name=first_name, last_name=last_name,
                                   email=email, phone=raw_phone)

        # Create user
        user = User(
            name=full_name,
            email=email,
            password=generate_password_hash(password),
            country_code="+63",
            phone=full_phone,
            role='guest'
        )
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

# -------------------- LOGOUT --------------------
@bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    if request.method == 'GET':
        return redirect(url_for('index'))
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# -------------------- PASSWORD RESET (LINK‑BASED) --------------------
@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not validate_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('forgot_pass.html')

        user = User.query.filter_by(email=email).first()
        if not user:
            # For security, don't reveal whether email exists
            flash('If that email is registered, you will receive a reset link.', 'info')
            return redirect(url_for('auth.login'))

        # Generate secure token
        token = secrets.token_urlsafe(32)
        PasswordReset.query.filter_by(email=email).delete()
        db.session.add(PasswordReset(email=email, token=token))
        db.session.commit()

        try:
            send_password_reset_email(email, token)   # sends link
            flash('Password reset link sent to your email.', 'success')
        except Exception as e:
            print(f"Error sending reset email: {e}")
            flash('Unable to send reset email. Please try again later.', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('forgot_pass.html')


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset = PasswordReset.query.filter_by(token=token).first()
    if not reset or reset.is_expired():
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        errors = []
        if not validate_password(password):
            errors.append("Password must be at least 8 characters with one uppercase, one lowercase, and one number.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('reset_password.html', token=token)

        user = User.query.filter_by(email=reset.email).first()
        if user:
            user.password = generate_password_hash(password)
            db.session.commit()
            db.session.delete(reset)
            db.session.commit()
            login_user(user)
            flash('Your password has been updated. You are now logged in.', 'success')
            if user.role == 'admin':
                return redirect(url_for('dashboard.admin_dashboard'))
            elif user.role == 'staff':
                return redirect(url_for('dashboard.staff_dashboard'))
            else:
                return redirect(url_for('dashboard.guest_dashboard'))
        else:
            flash('User not found. Please contact support.', 'danger')
            return redirect(url_for('auth.forgot_password'))

    return render_template('reset_password.html', token=token)

# -------------------- AJAX ENDPOINTS --------------------
@bp.route('/check-email')
def check_email():
    email = request.args.get('email', '').strip()
    if not email:
        return jsonify({'exists': False})
    user = User.query.filter_by(email=email).first()
    return jsonify({'exists': user is not None})

@bp.route('/check-phone')
def check_phone():
    phone = request.args.get('phone', '').strip()
    if not phone:
        return jsonify({'exists': False})
    # The frontend should send the full number (including +63)
    user = User.query.filter_by(phone=phone).first()
    return jsonify({'exists': user is not None})

# -------------------- TEST EMAIL (OPTIONAL) --------------------
@bp.route('/test-email')
def test_email():
    from flask_mail import Message
    from mail_config import mail
    try:
        msg = Message('Test', recipients=['your_test_email@example.com'])
        msg.body = 'This is a test'
        mail.send(msg)
        return 'Email sent!'
    except Exception as e:
        return f'Error: {e}'
import random
import string
from flask_mail import Message
from models import db, EmailVerification
from mail_config import mail
from flask import url_for

def send_verification_email(email):
    code = ''.join(random.choices(string.digits, k=6))
    EmailVerification.query.filter_by(email=email).delete()
    db.session.add(EmailVerification(email=email, code=code))
    db.session.commit()

    msg = Message('Email Verification', recipients=[email])
    msg.body = f'Your verification code is: {code}\nThis code expires in 10 minutes.'

    try:
        mail.send(msg)
        print(f"Email sent to {email} with code {code}")
        return code
    except Exception as e:
        print(f"FAILED to send email: {e}")
        # Still return the code for development so you can manually enter it
        return code

def send_password_reset_email(email, token):
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    msg = Message('Password Reset Request', recipients=[email])
    msg.body = f"""
    Hello,

    You requested to reset your password. Click the link below to set a new password:

    {reset_url}

    This link will expire in 10 minutes.

    If you did not request this, please ignore this email.
    """
    mail.send(msg)

def send_receipt_email(to_email, booking, receipt):
    subject = f"Booking Confirmation & Receipt - Booking #{booking.id}"
    body = f"""
    Dear {booking.user.name},

    Your booking (ID: {booking.id}) has been confirmed!
    Room: {booking.room.room_number} ({booking.room.room_type.name})
    Check-in: {booking.check_in}
    Check-out: {booking.check_out}
    Total: ₱{booking.total_amount:.2f}

    View your receipt online at:
    {url_for('bookings.view_receipt', booking_id=booking.id, _external=True)}

    Thank you for choosing us!
    """
    msg = Message(subject, recipients=[to_email])
    msg.body = body
    mail.send(msg)
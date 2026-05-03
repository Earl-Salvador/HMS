from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response, session
from flask_login import login_required, current_user, login_user
from models import db, Booking, Room, Coupon, User, Receipt
from datetime import datetime
from werkzeug.security import generate_password_hash
from utils.validators import validate_name, validate_email, validate_phone
from utils.receipt import generate_receipt
from utils.email_utils import send_receipt_email

bp = Blueprint('bookings', __name__, url_prefix='/booking')

# -------------------- GUEST BOOKING (no login required) --------------------
@bp.route('/book', methods=['GET', 'POST'])
def book():
    # Update room statuses before showing form
    if request.method == 'GET':
        Room.update_all_statuses()

    if request.method == 'POST':
        # Determine if user is a guest (not logged in)
        is_guest = not current_user.is_authenticated

        if is_guest:
            # Collect guest details
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            country_code = request.form.get('country_code', '+63')
            errors = []
            if not validate_name(name):
                errors.append("Name must be 2-50 characters (letters, spaces, hyphens, apostrophes).")
            if not validate_email(email):
                errors.append("Invalid email format.")
            if User.query.filter_by(email=email).first():
                errors.append("Email already registered. Please log in or use another email.")
            if phone and not validate_phone(phone):
                errors.append("Phone must be exactly 11 digits.")
            if errors:
                for err in errors:
                    flash(err, 'danger')
                rooms = Room.query.filter_by(status='available').all()
                return render_template('booking/book.html', rooms=rooms, guest_mode=True,
                                     name=name, email=email, phone=phone, country_code=country_code)
            # Create guest user with an empty password (cannot log in later)
            hashed_pw = generate_password_hash('')
            new_user = User(
                name=name,
                email=email,
                country_code=country_code,
                phone=phone,
                password=hashed_pw,
                role='guest'
            )
            db.session.add(new_user)
            db.session.commit()
            # Log the guest in automatically
            login_user(new_user)
            user_id = new_user.id
        else:
            user_id = current_user.id

        # Common booking creation
        room_id = request.form['room_id']
        check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d').date()
        coupon_code = request.form.get('coupon')

        room = Room.query.get(room_id)
        if not room or room.status != 'available':
            flash('Room not available', 'danger')
            return redirect(url_for('bookings.book'))

        # Check date overlap with confirmed bookings
        existing = Booking.query.filter_by(room_id=room_id, status='confirmed').filter(
            Booking.check_in < check_out, Booking.check_out > check_in
        ).first()
        if existing:
            flash('Room already booked for selected dates', 'danger')
            return redirect(url_for('bookings.book'))

        nights = (check_out - check_in).days
        if nights <= 0:
            flash('Invalid dates', 'danger')
            return redirect(url_for('bookings.book'))

        base_price = room.room_type.base_price
        total = base_price * nights

        # Apply coupon if valid
        if coupon_code:
            coupon = Coupon.query.filter_by(code=coupon_code, is_active=True).first()
            if coupon and coupon.valid_until >= datetime.now().date():
                discount = total * (coupon.discount_percent / 100)
                total -= discount
            else:
                flash('Invalid or expired coupon', 'warning')
                rooms = Room.query.filter_by(status='available').all()
                return render_template('booking/book.html', rooms=rooms, guest_mode=is_guest,
                                     name=name if is_guest else None,
                                     email=email if is_guest else None,
                                     phone=phone if is_guest else None,
                                     country_code=country_code if is_guest else None)

        booking = Booking(
            user_id=user_id,
            room_id=room_id,
            check_in=check_in,
            check_out=check_out,
            total_nights=nights,
            total_amount=total,
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()

        flash('Booking created! Proceed to payment.', 'success')
        return redirect(url_for('payments.pay', booking_id=booking.id))

    # GET – show booking form
    rooms = Room.query.filter_by(status='available').all()
    guest_mode = not current_user.is_authenticated
    response = make_response(render_template('booking/book.html', rooms=rooms, guest_mode=guest_mode))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# -------------------- CALENDAR (public) --------------------
@bp.route('/calendar')
def calendar():
    return render_template('booking/calendar.html')


@bp.route('/calendar-data')
def calendar_data():
    bookings = Booking.query.filter(Booking.status == 'confirmed').all()
    events = []
    for b in bookings:
        title = f"Room {b.room.room_number}"
        if current_user.is_authenticated:
            title += f" - {b.user.name}"
            if current_user.role == 'admin':
                title += f" ({b.total_nights} nights)"
        events.append({
            'title': title,
            'start': b.check_in.isoformat(),
            'end': b.check_out.isoformat(),
            'url': url_for('bookings.verify', booking_id=b.id),
            'backgroundColor': '#3788d8',
            'borderColor': '#3788d8',
            'extendedProps': {
                'guest': b.user.name,
                'nights': b.total_nights,
                'room': b.room.room_number,
                'check_in': b.check_in.strftime('%Y-%m-%d'),
                'check_out': b.check_out.strftime('%Y-%m-%d')
            }
        })
    return jsonify(events)


# -------------------- USER BOOKING VERIFICATION / CANCELLATION --------------------
@bp.route('/verify/<int:booking_id>')
@login_required
def verify(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    if booking.payment and booking.payment.status == 'completed':
        flash('Payment completed. Awaiting admin approval.', 'info')
    else:
        flash('Payment not completed yet.', 'warning')
    return redirect(url_for('dashboard.index'))


@bp.route('/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    if booking.status == 'cancelled':
        flash('Already cancelled', 'info')
    else:
        booking.status = 'cancelled'
        db.session.commit()
        booking.room.update_status()
        flash('Booking cancelled', 'success')
    return redirect(url_for('dashboard.index'))


@bp.route('/pending-count')
@login_required
def pending_count():
    if current_user.role != 'admin':
        return jsonify({'count': 0})
    count = Booking.query.filter_by(status='pending').count()
    return jsonify({'count': count})


# -------------------- ADMIN BOOKING VERIFICATION --------------------
@bp.route('/verify')
@login_required
def verify_bookings():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    bookings = Booking.query.filter_by(status='pending').order_by(Booking.created_at.desc()).all()
    for booking in bookings:
        booking.payment_status = 'completed' if (booking.payment and booking.payment.status == 'completed') else 'pending'
    return render_template('admin/verify_bookings.html', bookings=bookings)


@bp.route('/confirm/<int:booking_id>', methods=['POST'])
@login_required
def admin_confirm_booking(booking_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    booking = Booking.query.get_or_404(booking_id)
    if booking.status != 'pending':
        flash('Booking is not pending', 'warning')
        return redirect(url_for('bookings.verify_bookings'))
    if not booking.payment or booking.payment.status != 'completed':
        flash('Payment not completed yet. Cannot confirm booking.', 'danger')
        return redirect(url_for('bookings.verify_bookings'))

    booking.status = 'confirmed'
    db.session.commit()
    booking.room.update_status()

    receipt = generate_receipt(booking.id)
    send_receipt_email(booking.user.email, booking, receipt)

    flash(f'Booking #{booking.id} has been confirmed. Receipt sent to user.', 'success')
    return redirect(url_for('bookings.verify_bookings'))


@bp.route('/admin-cancel/<int:booking_id>', methods=['POST'])
@login_required
def admin_cancel_booking(booking_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    booking = Booking.query.get_or_404(booking_id)
    if booking.status != 'pending':
        flash('Booking is not pending', 'warning')
        return redirect(url_for('bookings.verify_bookings'))
    booking.status = 'cancelled'
    db.session.commit()
    booking.room.update_status()
    flash(f'Booking #{booking.id} has been cancelled.', 'success')
    return redirect(url_for('bookings.verify_bookings'))


@bp.route('/test-rooms')
@login_required
def test_rooms():
    Room.update_all_statuses()
    rooms = Room.query.filter_by(status='available').all()
    data = [{
        'id': r.id,
        'number': r.room_number,
        'type_name': r.room_type.name if r.room_type else None,
        'price': float(r.room_type.base_price) if r.room_type else None,
        'status': r.status
    } for r in rooms]
    return jsonify(data)


@bp.route('/receipt/<int:booking_id>')
@login_required
def view_receipt(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    receipt = Receipt.query.filter_by(booking_id=booking.id).first()
    if not receipt:
        receipt = generate_receipt(booking.id)

    return render_template('receipt.html', booking=booking, receipt=receipt)
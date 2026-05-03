from flask import Blueprint, render_template, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Booking, Payment, Comment, User, Room
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def index():
    """Redirect to the correct dashboard based on user role."""
    if current_user.role == 'admin':
        return redirect(url_for('dashboard.admin_dashboard'))
    elif current_user.role == 'staff':
        return redirect(url_for('dashboard.staff_dashboard'))
    else:
        return redirect(url_for('dashboard.guest_dashboard'))

@bp.route('/user_stats')
@login_required
def user_stats():
    # Total bookings for this user (confirmed only)
    total_bookings = Booking.query.filter_by(user_id=current_user.id, status='confirmed').count()
    # Upcoming bookings (check-in >= today, not cancelled)
    today = datetime.now().date()
    upcoming_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.status == 'confirmed',
        Booking.check_in >= today
    ).count()
    # Total spent (sum of completed payments for this user's bookings)
    total_spent = db.session.query(func.sum(Payment.amount)).join(Booking).filter(
        Booking.user_id == current_user.id,
        Payment.status == 'completed'
    ).scalar() or 0
    # Reviews given by user
    reviews_given = Comment.query.filter_by(user_id=current_user.id).count()

    return jsonify({
        'total_bookings': total_bookings,
        'upcoming_bookings': upcoming_bookings,
        'total_spent': float(total_spent),
        'reviews_given': reviews_given
    })

@bp.route('/recent_bookings')
@login_required
def recent_bookings():
    # For admin, show all recent bookings; for others, show their own
    if current_user.role == 'admin':
        bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    else:
        bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).limit(10).all()
    data = []
    for b in bookings:
        data.append({
            'id': b.id,
            'guest_name': b.user.name,
            'room_number': b.room.room_number,
            'check_in': b.check_in.strftime('%Y-%m-%d'),
            'check_out': b.check_out.strftime('%Y-%m-%d'),
            'status': b.status,
            'total_amount': float(b.total_amount)
        })
    return jsonify(data)

@bp.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    return render_template('dashboard/admin.html')

@bp.route('/staff')
@login_required
def staff_dashboard():
    if current_user.role not in ['admin', 'staff']:
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    return render_template('dashboard/staff.html')

@bp.route('/guest')
@login_required
def guest_dashboard():
    if current_user.role != 'guest':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    return render_template('dashboard/guest.html')

@bp.route('/admin_stats')
@login_required
def admin_stats():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Counts
    total_users = User.query.count()
    total_rooms = Room.query.count()
    total_bookings = Booking.query.filter_by(status='confirmed').count()
    total_revenue = db.session.query(func.sum(Payment.amount)).filter(Payment.status == 'completed').scalar() or 0
    
    # Occupancy for current month (just for a gauge)
    today = datetime.now().date()
    first_day = today.replace(day=1)
    if today.month == 12:
        last_day = today.replace(year=today.year+1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = today.replace(month=today.month+1, day=1) - timedelta(days=1)
    days_in_month = (last_day - first_day).days + 1
    total_room_nights = total_rooms * days_in_month
    occupied_nights = db.session.query(func.sum(Booking.total_nights)).filter(
        Booking.status == 'confirmed',
        Booking.check_in <= last_day,
        Booking.check_out >= first_day
    ).scalar() or 0
    occupancy_rate = (occupied_nights / total_room_nights) * 100 if total_room_nights > 0 else 0
    
    return jsonify({
        'total_users': total_users,
        'total_rooms': total_rooms,
        'total_bookings': total_bookings,
        'total_revenue': float(total_revenue),
        'occupancy_rate': round(occupancy_rate, 1)
    })
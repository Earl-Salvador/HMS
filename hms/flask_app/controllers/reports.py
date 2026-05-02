from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Booking, Payment
from sqlalchemy import func
from datetime import datetime

bp = Blueprint('reports', __name__, url_prefix='/reports')

@bp.route('/')
@login_required
def index():
    """Main reports page (admin/staff only)."""
    if current_user.role not in ['admin', 'staff']:
        return render_template('access_denied.html'), 403
    return render_template('admin/reports.html')

@bp.route('/booking-summary')
@login_required
def booking_summary():
    """Return JSON summary for reports, optionally filtered by date range."""
    if current_user.role not in ['admin', 'staff']:
        return jsonify({'error': 'Unauthorized'}), 403

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Base query for bookings (confirmed only)
    query = Booking.query.filter(Booking.status == 'confirmed')
    if start_date:
        query = query.filter(Booking.created_at >= start_date)
    if end_date:
        # include the end date (add one day to make it inclusive)
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(Booking.created_at <= end)

    total_bookings = query.count()

    # Total revenue from payments linked to those bookings
    payment_query = db.session.query(func.sum(Payment.amount)).join(Booking).filter(
        Booking.id == Payment.booking_id,
        Payment.status == 'completed'
    )
    if start_date:
        payment_query = payment_query.filter(Booking.created_at >= start_date)
    if end_date:
        payment_query = payment_query.filter(Booking.created_at <= end)
    total_revenue = payment_query.scalar() or 0

    avg_value = total_revenue / total_bookings if total_bookings > 0 else 0

    return jsonify({
        'total_bookings': total_bookings,
        'total_revenue': float(total_revenue),
        'average_booking_value': float(avg_value)
    })
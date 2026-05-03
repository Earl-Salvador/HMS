from flask import Blueprint, jsonify, render_template
from flask_login import login_required, current_user
from models import db, Booking, Room, Payment
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@bp.route('/occupancy')
@login_required
def occupancy_dashboard():
    return render_template('dashboard/occupancy.html')

@bp.route('/occupancy-data')
@login_required
def occupancy_data():
    end_date = datetime.now().date()
    rooms_count = Room.query.count()
    if rooms_count == 0:
        return jsonify({'labels': [], 'values': []})
    months = []
    rates = []
    for i in range(12):
        month_date = end_date.replace(day=1) - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(day=31)
        else:
            month_end = month_start.replace(month=month_start.month+1, day=1) - timedelta(days=1)
        total_nights = db.session.query(func.sum(Booking.total_nights)).filter(
            Booking.check_in <= month_end,
            Booking.check_out >= month_start,
            Booking.status == 'confirmed'
        ).scalar() or 0
        days_in_month = (month_end - month_start).days + 1
        available_room_nights = rooms_count * days_in_month
        occupancy_rate = (total_nights / available_room_nights) * 100 if available_room_nights > 0 else 0
        months.append(month_start.strftime('%b %Y'))
        rates.append(round(occupancy_rate, 2))
    months.reverse()
    rates.reverse()
    return jsonify({'labels': months, 'values': rates})

@bp.route('/revenue')
@login_required
def revenue_dashboard():
    return render_template('dashboard/revenue.html')

@bp.route('/revenue-data')
@login_required
def revenue_data():
    rooms = Room.query.all()
    result = {}
    for room in rooms:
        total_revenue = db.session.query(func.sum(Payment.amount)).join(Booking).filter(
            Booking.room_id == room.id,
            Payment.status == 'completed'
        ).scalar() or 0
        result[room.room_number] = float(total_revenue)
    return jsonify(result)

@bp.route('/trends')
@login_required
def trends_dashboard():
    return render_template('dashboard/trends.html')

@bp.route('/trends-data')
@login_required
def trends_data():
    end_date = datetime.now().date()
    months = []
    counts = []
    for i in range(12):
        month_date = end_date.replace(day=1) - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(day=31)
        else:
            month_end = month_start.replace(month=month_start.month+1, day=1) - timedelta(days=1)
        count = Booking.query.filter(
            Booking.check_in >= month_start,
            Booking.check_in <= month_end,
            Booking.status == 'confirmed'
        ).count()
        months.append(month_start.strftime('%b %Y'))
        counts.append(count)
    months.reverse()
    counts.reverse()
    return jsonify({'labels': months, 'values': counts})
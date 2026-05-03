from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Booking, Payment
from datetime import datetime
import requests
import json
from config import Config

bp = Blueprint('payments', __name__, url_prefix='/payment')

@bp.route('/pay/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def pay(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        payment_method = request.form['payment_method']
        # Simulate payment gateway success
        transaction_id = 'TXN' + str(datetime.utcnow().timestamp()).replace('.', '')

        # Prepare data for Java receipt service
        receipt_data = {
            'bookingId': booking.id,
            'roomType': booking.room.room_type.name,
            'nights': booking.total_nights,
            'basePrice': float(booking.room.room_type.base_price),
            'totalAmount': float(booking.total_amount),
            'taxRate': 12.0
        }

        try:
            # Call Java server
            response = requests.post(Config.JAVA_RECEIPT_URL, json=receipt_data, timeout=5)
            if response.status_code == 200:
                receipt = response.json()
                flash(f'Payment successful! Receipt ID: {receipt["receiptId"]}', 'success')
            else:
                flash('Payment processed but receipt service failed', 'warning')
        except Exception as e:
            flash(f'Payment processed but receipt service error: {str(e)}', 'warning')

        # Save payment record
        payment = Payment(
            booking_id=booking.id,
            amount=booking.total_amount,
            payment_method=payment_method,
            transaction_id=transaction_id,
            status='completed',
            paid_at=datetime.utcnow()
        )
        db.session.add(payment)
        booking.status = 'confirmed'
        db.session.commit()

        # In real app, send email/SMS here
        return redirect(url_for('dashboard.index'))

    return render_template('payment/pay.html', booking=booking)
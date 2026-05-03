from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_required, current_user
from models import db, Booking, Payment
from datetime import datetime

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
        # Simulate payment gateway success (replace with real PayMongo logic)
        transaction_id = 'TXN' + str(datetime.utcnow().timestamp()).replace('.', '')

        # Remove the Java receipt server call entirely
        # Save payment record
        # Save payment record – do NOT change booking status to 'confirmed'
        payment = Payment(
            booking_id=booking.id,
            amount=booking.total_amount,
            payment_method=payment_method,
            transaction_id=transaction_id,
            status='completed',
            paid_at=datetime.utcnow()
        )
        db.session.add(payment)
        # booking.status remains 'pending'
        db.session.commit()

        flash('Payment successful! Your booking is now pending admin approval.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('payment/pay.html', booking=booking)


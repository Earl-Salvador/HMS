import os
from datetime import datetime
from models import db, Receipt, Booking   # add Booking here

def generate_receipt(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return None

    receipt_number = f"INV-{booking_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    receipt = Receipt(
        booking_id=booking_id,
        receipt_number=receipt_number,
        pdf_path=''   # instead of None
    )
    db.session.add(receipt)
    db.session.commit()
    return receipt
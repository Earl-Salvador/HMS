from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta

db = SQLAlchemy()

# -------------------- USER & AUTH --------------------
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    country_code = db.Column(db.String(5), default='+63')
    phone = db.Column(db.String(20))
    role = db.Column(db.Enum('admin', 'staff', 'guest'), default='guest')
    is_blocked = db.Column(db.Boolean, default=False)   # NEW: for blocking users
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)


class EmailVerification(db.Model):
    __tablename__ = 'email_verifications'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_expired(self):
        return datetime.utcnow() > self.created_at + timedelta(minutes=10)


class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_expired(self):
        return datetime.utcnow() > self.created_at + timedelta(hours=1)


# -------------------- ROOMS & TYPES --------------------
class RoomType(db.Model):
    __tablename__ = 'room_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    base_price = db.Column(db.Numeric(10,2), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationships
    rooms = db.relationship('Room', back_populates='room_type', lazy=True)


class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    room_type_id = db.Column(db.Integer, db.ForeignKey('room_types.id'), nullable=False)
    status = db.Column(db.Enum('available', 'booked', 'maintenance'), default='available')
    # Relationships
    room_type = db.relationship('RoomType', back_populates='rooms', lazy=True)
    bookings = db.relationship('Booking', back_populates='room', lazy=True)

    def update_status(self):
        """Auto‑update room status based on active confirmed bookings."""
        if self.status == 'maintenance':
            return
        today = datetime.now().date()
        active_booking = Booking.query.filter(
            Booking.room_id == self.id,
            Booking.status == 'confirmed',
            Booking.check_in <= today,
            Booking.check_out > today
        ).first()
        new_status = 'booked' if active_booking else 'available'
        if self.status != new_status:
            self.status = new_status
            db.session.commit()

    @classmethod
    def update_all_statuses(cls):
        for room in cls.query.all():
            room.update_status()


# -------------------- BOOKINGS & PAYMENTS --------------------
class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    total_nights = db.Column(db.Integer, nullable=False, default=0)
    total_amount = db.Column(db.Numeric(10,2))
    status = db.Column(db.Enum('pending', 'confirmed', 'cancelled'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationships
    room = db.relationship('Room', back_populates='bookings', lazy=True)
    payment = db.relationship('Payment', backref='booking', uselist=False)
    # user and payment relationships are handled via backrefs or separately


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    amount = db.Column(db.Numeric(10,2), nullable=False)
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    status = db.Column(db.Enum('pending', 'completed', 'failed'), default='pending')
    paid_at = db.Column(db.DateTime)


# -------------------- AMENITIES & COMMENTS & COUPONS --------------------
class Amenity(db.Model):
    __tablename__ = 'amenities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    status = db.Column(db.Enum('pending', 'approved', 'declined'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Coupon(db.Model):
    __tablename__ = 'coupons'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percent = db.Column(db.Numeric(5,2))
    valid_until = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
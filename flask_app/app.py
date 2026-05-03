from flask import Flask, render_template
from config import Config
from flask_login import LoginManager, current_user
from werkzeug.security import generate_password_hash
from mail_config import mail
from models import db, User, Room, Booking, Payment, Comment
from datetime import datetime
from controllers import comments

app = Flask(__name__)
app.config.from_object(Config)
print(app.config['SQLALCHEMY_DATABASE_URI'])

db.init_app(app)
mail.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Import blueprints
from controllers import auth, bookings, rooms, amenities, users, comments, reports, analytics, payments, dashboard

app.register_blueprint(auth.bp)
app.register_blueprint(bookings.bp)
app.register_blueprint(rooms.bp)
app.register_blueprint(amenities.bp)
app.register_blueprint(users.bp)
app.register_blueprint(comments.bp, url_prefix='/comments')
app.register_blueprint(reports.bp)
app.register_blueprint(analytics.bp)
app.register_blueprint(payments.bp)
app.register_blueprint(dashboard.bp)


# -------------------- HOMEPAGE --------------------
@app.route('/')
def index():
    # Update room statuses first
    Room.update_all_statuses()
    
    # Get available rooms (only bookable ones)
    rooms = Room.query.filter_by(status='available').all()
    
    # Live stats
    total_rooms = Room.query.count()
    today = datetime.now().date()
    
    # Occupancy: rooms with a confirmed booking covering today
    occupied_rooms = Room.query.filter(
        Room.id.in_(
            db.session.query(Booking.room_id).filter(
                Booking.status == 'confirmed',
                Booking.check_in <= today,
                Booking.check_out > today
            )
        )
    ).count()
    occupancy = int((occupied_rooms / total_rooms) * 100) if total_rooms > 0 else 0
    
    # Today's revenue: sum of completed payments made today
    today_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.status == 'completed',
        db.func.date(Payment.paid_at) == today
    ).scalar() or 0
    
    # Pending bookings count (status='pending')
    pending_bookings = Booking.query.filter_by(status='pending').count()
    
    # Approved comments (max 6)
    approved_comments = Comment.query.filter_by(status='approved').order_by(Comment.created_at.desc()).limit(6).all()
    
    return render_template('index.html',
                         rooms=rooms,
                         occupancy=occupancy,
                         today_revenue=today_revenue,
                         pending_bookings=pending_bookings,
                         approved_comments=approved_comments)

# -------------------- MAIN --------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Sync room statuses before starting
        Room.update_all_statuses()
        # Create admin if not exists
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin_user = User(
                name='Admin',
                email='admin@hotel.com',
                password=generate_password_hash('admin123'),
                phone='1234567890',
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created: admin@hotel.com / admin123")
    app.run(debug=True)
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User
from werkzeug.security import generate_password_hash
from utils.validators import validate_name, validate_email, validate_phone, validate_password

bp = Blueprint('users', __name__, url_prefix='/admin/users')

@bp.route('/')
@login_required
def list_users():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@bp.route('/', methods=['POST'])
@login_required
def create_user():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json() or request.form
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password')
    phone = data.get('phone', '').strip()
    role = data.get('role', 'guest')

    # Validation
    if not validate_name(name):
        return jsonify({'error': 'Invalid name format'}), 400
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    if phone and not validate_phone(phone):
        return jsonify({'error': 'Phone must be exactly 11 digits'}), 400
    if not validate_password(password):
        return jsonify({'error': 'Password must be at least 8 characters with uppercase, lowercase, and a number'}), 400

    user = User(
        name=name,
        email=email,
        password=generate_password_hash(password),
        phone=phone,
        role=role
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True, 'id': user.id}), 201

@bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_user(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    user = User.query.get_or_404(id)
    data = request.get_json() or request.form
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    role = data.get('role', user.role)
    password = data.get('password')  # optional

    # Validation
    if not validate_name(name):
        return jsonify({'error': 'Invalid name format'}), 400
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    if email != user.email and User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered to another user'}), 400
    if phone and not validate_phone(phone):
        return jsonify({'error': 'Phone must be exactly 11 digits'}), 400
    if password and not validate_password(password):
        return jsonify({'error': 'Password must be at least 8 characters with uppercase, lowercase, and a number'}), 400

    user.name = name
    user.email = email
    user.phone = phone
    user.role = role
    if password:
        user.password = generate_password_hash(password)
    db.session.commit()
    return jsonify({'success': True}), 200

@bp.route('/block/<int:id>', methods=['POST'])
@login_required
def block_user(id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    user = User.query.get_or_404(id)
    if user.role == 'admin':
        flash('Cannot block another admin.', 'danger')
        return redirect(url_for('users.list_users'))
    if user.id == current_user.id:
        flash('You cannot block yourself.', 'danger')
        return redirect(url_for('users.list_users'))
    user.is_blocked = True
    db.session.commit()
    flash(f'User {user.name} has been blocked.', 'success')
    return redirect(url_for('users.list_users'))

@bp.route('/unblock/<int:id>', methods=['POST'])
@login_required
def unblock_user(id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    user = User.query.get_or_404(id)
    user.is_blocked = False
    db.session.commit()
    flash(f'User {user.name} has been unblocked.', 'success')
    return redirect(url_for('users.list_users'))

@bp.route('/<int:id>/json')
@login_required
def get_user_json(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    user = User.query.get_or_404(id)
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'phone': user.phone,
        'role': user.role
    })
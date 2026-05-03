from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Room, RoomType

bp = Blueprint('rooms', __name__, url_prefix='/admin/rooms')

# -------------------- ROOM TYPES --------------------
@bp.route('/room_types')
@login_required
def list_room_types():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    room_types = RoomType.query.all()
    return render_template('admin/room_types.html', room_types=room_types)

@bp.route('/room_types', methods=['POST'])
@login_required
def create_room_type():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json() or request.form
    name = data.get('name')
    description = data.get('description')
    base_price = data.get('base_price')
    capacity = data.get('capacity')
    if not name or not base_price or not capacity:
        return jsonify({'error': 'Missing required fields'}), 400
    rt = RoomType(name=name, description=description, base_price=base_price, capacity=capacity)
    db.session.add(rt)
    db.session.commit()
    return jsonify({'success': True, 'id': rt.id}), 201

@bp.route('/room_types/<int:id>', methods=['PUT'])
@login_required
def update_room_type(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    rt = RoomType.query.get_or_404(id)
    data = request.get_json() or request.form
    rt.name = data.get('name', rt.name)
    rt.description = data.get('description', rt.description)
    rt.base_price = data.get('base_price', rt.base_price)
    rt.capacity = data.get('capacity', rt.capacity)
    db.session.commit()
    return jsonify({'success': True}), 200

@bp.route('/room_types/<int:id>', methods=['DELETE'])
@login_required
def delete_room_type(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    rt = RoomType.query.get_or_404(id)
    # Prevent deletion if any rooms use this type
    if rt.rooms and len(rt.rooms) > 0:
        return jsonify({'success': False, 'error': 'Cannot delete room type because rooms are using it.'}), 400
    db.session.delete(rt)
    db.session.commit()
    return jsonify({'success': True}), 200

@bp.route('/room_types/<int:id>/json')
@login_required
def get_room_type_json(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    rt = RoomType.query.get_or_404(id)
    return jsonify({
        'id': rt.id,
        'name': rt.name,
        'description': rt.description,
        'base_price': float(rt.base_price),
        'capacity': rt.capacity
    })

# -------------------- ROOMS --------------------
@bp.route('/rooms')
@login_required
def list_rooms():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    rooms = Room.query.all()
    room_types = RoomType.query.all()
    return render_template('admin/rooms.html', rooms=rooms, room_types=room_types)

@bp.route('/rooms', methods=['POST'])
@login_required
def create_room():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    room_number = data.get('room_number')
    room_type_id = data.get('room_type_id')
    status = data.get('status', 'available')

    if not room_number or not room_type_id:
        return jsonify({'error': 'Room number and room type are required'}), 400

    # Check for duplicate room number
    if Room.query.filter_by(room_number=room_number).first():
        return jsonify({'error': f'Room number {room_number} already exists'}), 400

    # Verify room type exists
    room_type = RoomType.query.get(room_type_id)
    if not room_type:
        return jsonify({'error': 'Invalid room type'}), 400

    new_room = Room(
        room_number=room_number,
        room_type_id=room_type_id,
        status=status
    )
    db.session.add(new_room)
    db.session.commit()
    return jsonify({'success': True, 'id': new_room.id}), 201

@bp.route('/rooms/<int:id>', methods=['PUT'])
@login_required
def update_room(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    room = Room.query.get_or_404(id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    new_number = data.get('room_number', room.room_number)
    # Check unique room number
    if new_number != room.room_number and Room.query.filter_by(room_number=new_number).first():
        return jsonify({'error': 'Room number already exists'}), 400

    room.room_number = new_number
    room.room_type_id = data.get('room_type_id', room.room_type_id)
    room.status = data.get('status', room.status)
    db.session.commit()
    return jsonify({'success': True}), 200

@bp.route('/rooms/<int:id>', methods=['DELETE'])
@login_required
def delete_room(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    room = Room.query.get_or_404(id)
    # Check if the room has any bookings
    if room.bookings and len(room.bookings) > 0:
        return jsonify({'success': False, 'error': 'Cannot delete room because it has existing bookings.'}), 400
    db.session.delete(room)
    db.session.commit()
    return jsonify({'success': True}), 200

@bp.route('/rooms/<int:id>/json')
@login_required
def get_room_json(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    room = Room.query.get_or_404(id)
    return jsonify({
        'id': room.id,
        'room_number': room.room_number,
        'room_type_id': room.room_type_id,
        'status': room.status,
        'room_type_name': room.room_type.name if room.room_type else ''
    })
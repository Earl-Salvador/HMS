from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Amenity

bp = Blueprint('amenities', __name__, url_prefix='/admin/amenities')

@bp.route('/')
@login_required
def list_amenities():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    amenities = Amenity.query.all()
    return render_template('admin/amenities.html', amenities=amenities)

@bp.route('/', methods=['POST'])
@login_required
def create_amenity():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json() or request.form
    name = data.get('name')
    icon = data.get('icon', 'fa-hotel')
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    amenity = Amenity(name=name, icon=icon)
    db.session.add(amenity)
    db.session.commit()
    return jsonify({'success': True, 'id': amenity.id}), 201

@bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_amenity(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    amenity = Amenity.query.get_or_404(id)
    data = request.get_json() or request.form
    amenity.name = data.get('name', amenity.name)
    amenity.icon = data.get('icon', amenity.icon)
    db.session.commit()
    return jsonify({'success': True}), 200

@bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_amenity(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    amenity = Amenity.query.get_or_404(id)
    db.session.delete(amenity)
    db.session.commit()
    return jsonify({'success': True}), 200

@bp.route('/<int:id>/json')
@login_required
def get_amenity_json(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    amenity = Amenity.query.get_or_404(id)
    return jsonify({
        'id': amenity.id,
        'name': amenity.name,
        'icon': amenity.icon
    })
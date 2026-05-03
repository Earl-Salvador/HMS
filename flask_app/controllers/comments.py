from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Comment, Booking

bp = Blueprint('comments', __name__, url_prefix='/comments')   # change prefix to /comments for general access

# -------------------- ADMIN ROUTES (prefix: /admin/comments) --------------------
# We keep these under /admin/comments but the blueprint prefix is now '/comments'
# Actually better to split: admin routes under /admin/comments, user routes under /comments.
# For simplicity, we'll keep all under /comments but add role checks.

@bp.route('/')
@login_required
def list_comments():
    """Admin only: list comments filtered by status."""
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    status = request.args.get('status', 'all')
    if status == 'all':
        comments = Comment.query.order_by(Comment.created_at.desc()).all()
    else:
        comments = Comment.query.filter_by(status=status).order_by(Comment.created_at.desc()).all()
    return render_template('admin/comments.html', comments=comments, current_filter=status)


@bp.route('/approve/<int:id>', methods=['POST'])
@login_required
def approve_comment(id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    comment = Comment.query.get_or_404(id)
    comment.status = 'approved'
    db.session.commit()
    flash('Comment approved and will now be visible.', 'success')
    return redirect(url_for('comments.list_comments'))


@bp.route('/archive/<int:id>', methods=['POST'])
@login_required
def archive_comment(id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    comment = Comment.query.get_or_404(id)
    comment.status = 'archived'
    db.session.commit()
    flash('Comment has been archived and will no longer be visible.', 'success')
    return redirect(url_for('comments.list_comments'))


@bp.route('/delete/<int:id>', methods=['DELETE'])
@login_required
def delete_comment(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'success': True}), 200


# -------------------- USER / GUEST ROUTES --------------------
@bp.route('/user-bookings')
@login_required
def user_bookings():
    """Return JSON of user's confirmed bookings without a comment yet."""
    bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.status == 'confirmed',
        ~Booking.comment.has()
    ).all()
    data = [{
        'id': b.id,
        'room_number': b.room.room_number,
        'check_in': b.check_in.strftime('%Y-%m-%d'),
        'check_out': b.check_out.strftime('%Y-%m-%d')
    } for b in bookings]
    return jsonify(data)


@bp.route('/add-ajax', methods=['POST'])
def add_comment_ajax():
    """AJAX endpoint for submitting comments from modal (logged-in or guest)."""
    if current_user.is_authenticated:
        # Logged-in user
        booking_id = request.form.get('booking_id')
        rating = request.form.get('rating')
        comment_text = request.form.get('comment')
        if not all([booking_id, rating, comment_text]):
            return jsonify({'success': False, 'error': 'All fields are required.'})
        booking = Booking.query.get(booking_id)
        if not booking or booking.user_id != current_user.id or booking.status != 'confirmed':
            return jsonify({'success': False, 'error': 'Invalid booking or not yet confirmed.'})
        existing = Comment.query.filter_by(booking_id=booking_id).first()
        if existing:
            return jsonify({'success': False, 'error': 'You already reviewed this booking.'})
        comment = Comment(
            user_id=current_user.id,
            booking_id=booking_id,
            rating=int(rating),
            comment=comment_text,
            status='pending'
        )
        db.session.add(comment)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Thank you! Your review will be approved soon.'})
    else:
        # Guest submission
        booking_id = request.form.get('booking_id')
        guest_name = request.form.get('guest_name')
        guest_email = request.form.get('guest_email')
        rating = request.form.get('rating')
        comment_text = request.form.get('comment')
        if not all([booking_id, guest_name, guest_email, rating, comment_text]):
            return jsonify({'success': False, 'error': 'All fields are required.'})
        booking = Booking.query.get(booking_id)
        if not booking or booking.status != 'confirmed':
            return jsonify({'success': False, 'error': 'Invalid booking ID or booking not completed.'})
        # Optional email match check (if booking has a user)
        if booking.user and booking.user.email.lower() != guest_email.lower():
            return jsonify({'success': False, 'error': 'Email does not match the booking record.'})
        comment = Comment(
            booking_id=booking_id,
            rating=int(rating),
            comment=comment_text,
            guest_name=guest_name,
            guest_email=guest_email,
            status='pending'
        )
        db.session.add(comment)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Your review has been submitted and will appear after approval.'})


# -------------------- TRADITIONAL FORM (optional, kept for fallback) --------------------
@bp.route('/add', methods=['GET', 'POST'])
def add_comment():
    """Traditional form for adding comments (non‑AJAX)."""
    if request.method == 'GET':
        if current_user.is_authenticated:
            bookings = Booking.query.filter(
                Booking.user_id == current_user.id,
                Booking.status == 'confirmed',
                ~Booking.comment.has()
            ).all()
            return render_template('comment_form.html', bookings=bookings, guest_mode=False)
        else:
            return render_template('comment_form.html', guest_mode=True)
    else:
        # POST – handled by AJAX; this remains for non‑JS fallback (unlikely used)
        return redirect(url_for('index'))
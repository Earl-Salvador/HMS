from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Comment

bp = Blueprint('comments', __name__, url_prefix='/admin/comments')

# -------------------- LIST COMMENTS (with filter) --------------------
@bp.route('/')
@login_required
def list_comments():
    """List comments filtered by status (admin only)."""
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))

    status = request.args.get('status', 'all')
    if status == 'all':
        comments = Comment.query.order_by(Comment.created_at.desc()).all()
    else:
        comments = Comment.query.filter_by(status=status).order_by(Comment.created_at.desc()).all()

    return render_template('admin/comments.html', comments=comments, current_filter=status)


# -------------------- APPROVE COMMENT --------------------
@bp.route('/approve/<int:id>', methods=['POST'])
@login_required
def approve_comment(id):
    """Approve a pending comment."""
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    comment = Comment.query.get_or_404(id)
    comment.status = 'approved'
    db.session.commit()
    flash('Comment approved and will now be visible.', 'success')
    return redirect(url_for('comments.list_comments'))


# -------------------- DECLINE COMMENT --------------------
@bp.route('/decline/<int:id>', methods=['POST'])
@login_required
def decline_comment(id):
    """Decline a pending comment."""
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    comment = Comment.query.get_or_404(id)
    comment.status = 'declined'
    db.session.commit()
    flash('Comment declined and will not be shown.', 'success')
    return redirect(url_for('comments.list_comments'))


# -------------------- DELETE COMMENT (AJAX) --------------------
@bp.route('/delete/<int:id>', methods=['DELETE'])
@login_required
def delete_comment(id):
    """Delete a comment permanently (AJAX)."""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'success': True}), 200
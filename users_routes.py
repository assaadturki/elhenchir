# -*- coding: utf-8 -*-
"""
Routes de gestion des utilisateurs + décorateurs de rôles.
Ajouter ces imports et routes dans app.py
"""

from functools import wraps
from flask import abort
from flask_login import current_user


# ========== DÉCORATEURS DE RÔLES ==========

def admin_required(f):
    """Route accessible uniquement par l'admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def manager_required(f):
    """Route accessible par admin et manager."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'manager']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def employee_required(f):
    """Route accessible par tous les rôles connectés."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


# ========== ROUTES USERS ==========

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.date_creation.desc()).all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_user():
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()

            # Vérifier email unique
            if User.query.filter_by(email=email).first():
                flash('Cet email est déjà utilisé.', 'danger')
                return render_template('admin/create_user.html')

            user = User(
                nom=request.form.get('nom'),
                email=email,
                role=request.form.get('role', 'employee'),
                telephone=request.form.get('telephone'),
                adresse=request.form.get('adresse'),
                is_active=True
            )
            user.set_password(request.form.get('password'))
            db.session.add(user)
            db.session.commit()
            flash(f'Utilisateur {user.nom} créé avec succès!', 'success')
            return redirect(url_for('admin_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')

    return render_template('admin/create_user.html')


@app.route('/admin/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(id):
    user = db.get_or_404(User, id)

    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()

            # Vérifier email unique (exclure l'utilisateur actuel)
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != user.id:
                flash('Cet email est déjà utilisé.', 'danger')
                return render_template('admin/edit_user.html', user=user)

            user.nom = request.form.get('nom')
            user.email = email
            user.role = request.form.get('role')
            user.telephone = request.form.get('telephone')
            user.adresse = request.form.get('adresse')
            user.is_active = request.form.get('is_active') == 'on'

            # Changer le mot de passe seulement si rempli
            new_password = request.form.get('password', '').strip()
            if new_password:
                user.set_password(new_password)

            db.session.commit()
            flash(f'Utilisateur {user.nom} modifié avec succès!', 'success')
            return redirect(url_for('admin_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')

    return render_template('admin/edit_user.html', user=user)


@app.route('/admin/users/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_toggle_user(id):
    user = db.get_or_404(User, id)

    # Empêcher l'admin de se désactiver lui-même
    if user.id == current_user.id:
        return jsonify({'success': False, 'error': 'Vous ne pouvez pas vous désactiver vous-même.'}), 400

    try:
        user.is_active = not user.is_active
        db.session.commit()
        status = 'activé' if user.is_active else 'désactivé'
        return jsonify({'success': True, 'status': status, 'is_active': user.is_active})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/users/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(id):
    user = db.get_or_404(User, id)

    if user.id == current_user.id:
        return jsonify({'success': False, 'error': 'Vous ne pouvez pas supprimer votre propre compte.'}), 400

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/users/reset-password/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_reset_password(id):
    user = db.get_or_404(User, id)
    try:
        new_password = request.form.get('new_password', '').strip()
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'Mot de passe trop court (min 6 caractères).'}), 400
        user.set_password(new_password)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== PAGE PROFIL (pour tous les users) ==========

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            current_user.nom = request.form.get('nom')
            current_user.telephone = request.form.get('telephone')
            current_user.adresse = request.form.get('adresse')

            old_password = request.form.get('old_password', '').strip()
            new_password = request.form.get('new_password', '').strip()

            if old_password and new_password:
                if not current_user.check_password(old_password):
                    flash('Ancien mot de passe incorrect.', 'danger')
                    return render_template('admin/profile.html')
                if len(new_password) < 6:
                    flash('Nouveau mot de passe trop court (min 6 caractères).', 'danger')
                    return render_template('admin/profile.html')
                current_user.set_password(new_password)
                flash('Mot de passe modifié avec succès!', 'success')

            db.session.commit()
            flash('Profil mis à jour!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')

    return render_template('admin/profile.html')


# ========== ERREUR 403 ==========

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

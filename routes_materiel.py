# -*- coding: utf-8 -*-
# ========== AJOUTER DANS app.py ==========
# 1. Dans les imports en haut :
#    from werkzeug.utils import secure_filename
# 2. Coller tout ce bloc avant "if __name__ == '__main__':"

import uuid
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_facture(file):
    """Sauvegarde une facture et retourne le nom du fichier."""
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename):
        return None
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    factures_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'factures')
    os.makedirs(factures_dir, exist_ok=True)
    file.save(os.path.join(factures_dir, filename))
    return filename


# ========== UPLOAD FACTURES ==========

@app.route('/uploads/factures/<path:filename>')
@login_required
def serve_facture(filename):
    factures_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'factures')
    return send_from_directory(factures_dir, filename)


# ========== DEPENSES : modifier create_expense pour ajouter upload ==========
# Remplacer la route /expenses/create existante par celle-ci :

@app.route('/expenses/create', methods=['GET', 'POST'])
@login_required
@manager_required
def create_expense():
    plots = Plot.query.all()
    categories = ['Semences', 'Engrais', 'Eau', 'Carburant', 'Salaires',
                  'Transport', 'Reparation materiel', 'Electricite',
                  'Produits veterinaires', 'Nourriture animale', 'Loyer', 'Assurances', 'Autre']
    if request.method == 'POST':
        try:
            # Upload facture
            facture_fichier = None
            if 'facture' in request.files:
                facture_fichier = save_facture(request.files['facture'])

            expense = Expense(
                categorie=request.form.get('categorie'),
                montant_tnd=float(request.form.get('montant_tnd')),
                date_depense=datetime.strptime(request.form.get('date_depense'), '%Y-%m-%d').date(),
                description=request.form.get('description'),
                parcelle_id=int(request.form.get('parcelle_id')) if request.form.get('parcelle_id') else None,
                fournisseur=request.form.get('fournisseur'),
                reference=request.form.get('reference'),
                facture_fichier=facture_fichier
            )
            db.session.add(expense)
            db.session.commit()
            flash('Depense ajoutee avec succes!', 'success')
            return redirect(url_for('expenses'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    return render_template('expenses/create.html', plots=plots, categories=categories, now=datetime.now())


@app.route('/expenses/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@manager_required
def edit_expense(id):
    expense = db.get_or_404(Expense, id)
    plots = Plot.query.all()
    categories = ['Semences', 'Engrais', 'Eau', 'Carburant', 'Salaires',
                  'Transport', 'Reparation materiel', 'Electricite',
                  'Produits veterinaires', 'Nourriture animale', 'Loyer', 'Assurances', 'Autre']
    if request.method == 'POST':
        try:
            if 'facture' in request.files and request.files['facture'].filename:
                new_facture = save_facture(request.files['facture'])
                if new_facture:
                    expense.facture_fichier = new_facture

            expense.categorie = request.form.get('categorie')
            expense.montant_tnd = float(request.form.get('montant_tnd'))
            expense.date_depense = datetime.strptime(request.form.get('date_depense'), '%Y-%m-%d').date()
            expense.description = request.form.get('description')
            expense.parcelle_id = int(request.form.get('parcelle_id')) if request.form.get('parcelle_id') else None
            expense.fournisseur = request.form.get('fournisseur')
            expense.reference = request.form.get('reference')
            db.session.commit()
            flash('Depense modifiee avec succes!', 'success')
            return redirect(url_for('expenses'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    return render_template('expenses/edit.html', expense=expense, plots=plots, categories=categories)


@app.route('/expenses/delete/<int:id>', methods=['POST'])
@login_required
@manager_required
def delete_expense(id):
    expense = db.get_or_404(Expense, id)
    try:
        db.session.delete(expense)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== MATERIEL AGRICOLE ==========

@app.route('/materiel')
@login_required
def materiel():
    all_materiel = Materiel.query.all()
    entretiens_proches = EntretienMateriel.query.filter(
        EntretienMateriel.date_prochain <= (datetime.now().date() + timedelta(days=30))
    ).order_by(EntretienMateriel.date_prochain).all()
    return render_template('materiel/index.html', materiels=all_materiel, entretiens_proches=entretiens_proches)


@app.route('/materiel/create', methods=['GET', 'POST'])
@login_required
@manager_required
def create_materiel():
    plots = Plot.query.all()
    types = ['Tracteur', 'Charrue', 'Semoir', 'Moissonneuse', 'Pompe irrigation',
             'Pulverisateur', 'Remorque', 'Motoculteur', 'Generateur', 'Autre']
    etats = [('bon', 'Bon'), ('moyen', 'Moyen'), ('mauvais', 'Mauvais'), ('hors_service', 'Hors service')]

    if request.method == 'POST':
        try:
            materiel = Materiel(
                nom=request.form.get('nom'),
                type_materiel=request.form.get('type_materiel'),
                marque=request.form.get('marque'),
                modele=request.form.get('modele'),
                numero_serie=request.form.get('numero_serie') or None,
                annee_achat=int(request.form.get('annee_achat')) if request.form.get('annee_achat') else None,
                prix_achat=float(request.form.get('prix_achat')) if request.form.get('prix_achat') else None,
                etat=request.form.get('etat', 'bon'),
                parcelle_id=int(request.form.get('parcelle_id')) if request.form.get('parcelle_id') else None,
                localisation=request.form.get('localisation'),
                notes=request.form.get('notes')
            )
            db.session.add(materiel)
            db.session.flush()

            # Enregistrer le coût d'achat
            prix_achat = float(request.form.get('prix_achat')) if request.form.get('prix_achat') else 0
            if prix_achat > 0:
                cout = CoutMateriel(
                    materiel_id=materiel.id,
                    type_cout='achat',
                    montant_tnd=prix_achat,
                    date_cout=datetime.now().date(),
                    description=f"Achat: {materiel.nom}"
                )
                db.session.add(cout)

            db.session.commit()
            flash('Materiel ajoute avec succes!', 'success')
            return redirect(url_for('materiel'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    return render_template('materiel/create.html', plots=plots, types=types, etats=etats, now=datetime.now())


@app.route('/materiel/<int:id>')
@login_required
def materiel_detail(id):
    mat = db.get_or_404(Materiel, id)
    entretiens = EntretienMateriel.query.filter_by(materiel_id=id).order_by(EntretienMateriel.date_entretien.desc()).all()
    pannes = PanneMateriel.query.filter_by(materiel_id=id).order_by(PanneMateriel.date_panne.desc()).all()
    couts = CoutMateriel.query.filter_by(materiel_id=id).order_by(CoutMateriel.date_cout.desc()).all()
    total_couts = sum(float(c.montant_tnd) for c in couts)
    return render_template('materiel/detail.html', mat=mat, entretiens=entretiens,
                           pannes=pannes, couts=couts, total_couts=total_couts, now=datetime.now())


@app.route('/materiel/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@manager_required
def edit_materiel(id):
    mat = db.get_or_404(Materiel, id)
    plots = Plot.query.all()
    types = ['Tracteur', 'Charrue', 'Semoir', 'Moissonneuse', 'Pompe irrigation',
             'Pulverisateur', 'Remorque', 'Motoculteur', 'Generateur', 'Autre']
    etats = [('bon', 'Bon'), ('moyen', 'Moyen'), ('mauvais', 'Mauvais'), ('hors_service', 'Hors service')]

    if request.method == 'POST':
        try:
            mat.nom = request.form.get('nom')
            mat.type_materiel = request.form.get('type_materiel')
            mat.marque = request.form.get('marque')
            mat.modele = request.form.get('modele')
            mat.numero_serie = request.form.get('numero_serie') or None
            mat.annee_achat = int(request.form.get('annee_achat')) if request.form.get('annee_achat') else None
            mat.prix_achat = float(request.form.get('prix_achat')) if request.form.get('prix_achat') else None
            mat.etat = request.form.get('etat')
            mat.parcelle_id = int(request.form.get('parcelle_id')) if request.form.get('parcelle_id') else None
            mat.localisation = request.form.get('localisation')
            mat.notes = request.form.get('notes')
            db.session.commit()
            flash('Materiel modifie avec succes!', 'success')
            return redirect(url_for('materiel_detail', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    return render_template('materiel/edit.html', mat=mat, plots=plots, types=types, etats=etats)


@app.route('/materiel/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_materiel(id):
    mat = db.get_or_404(Materiel, id)
    try:
        db.session.delete(mat)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# --- Entretiens ---
@app.route('/materiel/entretien/add/<int:materiel_id>', methods=['GET', 'POST'])
@login_required
@manager_required
def add_entretien(materiel_id):
    mat = db.get_or_404(Materiel, materiel_id)
    types_entretien = ['Vidange', 'Revision generale', 'Graissage', 'Remplacement filtre',
                       'Remplacement courroie', 'Verification electrique', 'Autre']

    if request.method == 'POST':
        try:
            cout = float(request.form.get('cout_tnd')) if request.form.get('cout_tnd') else 0
            entretien = EntretienMateriel(
                materiel_id=materiel_id,
                type_entretien=request.form.get('type_entretien'),
                date_entretien=datetime.strptime(request.form.get('date_entretien'), '%Y-%m-%d').date(),
                date_prochain=datetime.strptime(request.form.get('date_prochain'), '%Y-%m-%d').date() if request.form.get('date_prochain') else None,
                description=request.form.get('description'),
                technicien=request.form.get('technicien'),
                cout_tnd=cout,
                pieces_changees=request.form.get('pieces_changees'),
                notes=request.form.get('notes')
            )
            db.session.add(entretien)

            if cout > 0:
                cout_mat = CoutMateriel(
                    materiel_id=materiel_id,
                    type_cout='reparation',
                    montant_tnd=cout,
                    date_cout=datetime.strptime(request.form.get('date_entretien'), '%Y-%m-%d').date(),
                    description=f"Entretien: {request.form.get('type_entretien')}"
                )
                db.session.add(cout_mat)

                expense = Expense(
                    categorie='Reparation materiel',
                    montant_tnd=cout,
                    date_depense=datetime.strptime(request.form.get('date_entretien'), '%Y-%m-%d').date(),
                    description=f"Entretien {mat.nom}: {request.form.get('type_entretien')}",
                    fournisseur=request.form.get('technicien')
                )
                db.session.add(expense)

            db.session.commit()
            flash('Entretien enregistre avec succes!', 'success')
            return redirect(url_for('materiel_detail', id=materiel_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')

    return render_template('materiel/add_entretien.html', mat=mat, types_entretien=types_entretien, now=datetime.now())


# --- Pannes ---
@app.route('/materiel/panne/add/<int:materiel_id>', methods=['GET', 'POST'])
@login_required
@manager_required
def add_panne(materiel_id):
    mat = db.get_or_404(Materiel, materiel_id)

    if request.method == 'POST':
        try:
            cout = float(request.form.get('cout_reparation')) if request.form.get('cout_reparation') else 0
            panne = PanneMateriel(
                materiel_id=materiel_id,
                date_panne=datetime.strptime(request.form.get('date_panne'), '%Y-%m-%d').date(),
                date_reparation=datetime.strptime(request.form.get('date_reparation'), '%Y-%m-%d').date() if request.form.get('date_reparation') else None,
                description=request.form.get('description'),
                cause=request.form.get('cause'),
                technicien=request.form.get('technicien'),
                cout_reparation=cout,
                statut=request.form.get('statut', 'en_cours'),
                notes=request.form.get('notes')
            )
            db.session.add(panne)

            # Mettre à jour l'état du matériel
            if panne.statut == 'en_cours':
                mat.etat = 'hors_service'
            elif panne.statut == 'repare':
                mat.etat = 'bon'

            if cout > 0:
                cout_mat = CoutMateriel(
                    materiel_id=materiel_id,
                    type_cout='reparation',
                    montant_tnd=cout,
                    date_cout=datetime.strptime(request.form.get('date_panne'), '%Y-%m-%d').date(),
                    description=f"Reparation panne: {request.form.get('description')[:50]}"
                )
                db.session.add(cout_mat)

                expense = Expense(
                    categorie='Reparation materiel',
                    montant_tnd=cout,
                    date_depense=datetime.strptime(request.form.get('date_panne'), '%Y-%m-%d').date(),
                    description=f"Reparation {mat.nom}: {request.form.get('description')[:100]}",
                    fournisseur=request.form.get('technicien')
                )
                db.session.add(expense)

            db.session.commit()
            flash('Panne enregistree avec succes!', 'success')
            return redirect(url_for('materiel_detail', id=materiel_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')

    return render_template('materiel/add_panne.html', mat=mat, now=datetime.now())


# --- Coûts carburant ---
@app.route('/materiel/cout/add/<int:materiel_id>', methods=['GET', 'POST'])
@login_required
@manager_required
def add_cout_materiel(materiel_id):
    mat = db.get_or_404(Materiel, materiel_id)
    types_cout = [('carburant', 'Carburant'), ('reparation', 'Reparation'),
                  ('piece', 'Piece de rechange'), ('assurance', 'Assurance'), ('autre', 'Autre')]

    if request.method == 'POST':
        try:
            montant = float(request.form.get('montant_tnd'))
            type_cout = request.form.get('type_cout')
            date_cout = datetime.strptime(request.form.get('date_cout'), '%Y-%m-%d').date()

            cout = CoutMateriel(
                materiel_id=materiel_id,
                type_cout=type_cout,
                montant_tnd=montant,
                date_cout=date_cout,
                description=request.form.get('description'),
                notes=request.form.get('notes')
            )
            db.session.add(cout)

            cat_map = {'carburant': 'Carburant', 'reparation': 'Reparation materiel',
                       'piece': 'Reparation materiel', 'assurance': 'Assurances', 'autre': 'Autre'}
            expense = Expense(
                categorie=cat_map.get(type_cout, 'Autre'),
                montant_tnd=montant,
                date_depense=date_cout,
                description=f"{type_cout.capitalize()} - {mat.nom}: {request.form.get('description') or ''}"
            )
            db.session.add(expense)

            db.session.commit()
            flash('Cout enregistre avec succes!', 'success')
            return redirect(url_for('materiel_detail', id=materiel_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')

    return render_template('materiel/add_cout.html', mat=mat, types_cout=types_cout, now=datetime.now())

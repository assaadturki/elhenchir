# -*- coding: utf-8 -*-
# ========== ROUTES PROPRIETAIRES ==========
# Ajouter dans app.py avant "if __name__ == '__main__':"
# Aussi ajouter dans les imports models:
#   Proprietaire, PartProprietaire, DepenseProprietaire

# ========== CRUD PROPRIETAIRES ==========

@app.route('/proprietaires')
@login_required
def proprietaires():
    all_props = Proprietaire.query.order_by(Proprietaire.nom).all()
    return render_template('proprietaires/index.html', proprietaires=all_props)


@app.route('/proprietaires/create', methods=['GET', 'POST'])
@login_required
@manager_required
def create_proprietaire():
    if request.method == 'POST':
        try:
            prop = Proprietaire(
                nom=request.form.get('nom'),
                prenom=request.form.get('prenom'),
                telephone=request.form.get('telephone'),
                email=request.form.get('email'),
                adresse=request.form.get('adresse'),
                notes=request.form.get('notes')
            )
            db.session.add(prop)
            db.session.commit()
            flash(f'Propriétaire {prop.nom} ajouté avec succès!', 'success')
            return redirect(url_for('proprietaires'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    return render_template('proprietaires/create.html')


@app.route('/proprietaires/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@manager_required
def edit_proprietaire(id):
    prop = db.get_or_404(Proprietaire, id)
    if request.method == 'POST':
        try:
            prop.nom = request.form.get('nom')
            prop.prenom = request.form.get('prenom')
            prop.telephone = request.form.get('telephone')
            prop.email = request.form.get('email')
            prop.adresse = request.form.get('adresse')
            prop.notes = request.form.get('notes')
            db.session.commit()
            flash('Propriétaire modifié!', 'success')
            return redirect(url_for('proprietaires'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    return render_template('proprietaires/edit.html', prop=prop)


@app.route('/proprietaires/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_proprietaire(id):
    prop = db.get_or_404(Proprietaire, id)
    try:
        db.session.delete(prop)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== TABLEAU DE BORD PAR PROPRIETAIRE ==========

@app.route('/proprietaires/<int:id>/dashboard')
@login_required
def proprietaire_dashboard(id):
    prop = db.get_or_404(Proprietaire, id)

    # Récupérer toutes les parts de ce propriétaire
    parts = PartProprietaire.query.filter_by(proprietaire_id=id).all()

    # Calculer les biens possédés
    biens = {'parcelle': [], 'animal': [], 'olivier': [], 'materiel': []}
    for part in parts:
        biens[part.type_bien].append({
            'part': part,
            'part_pct': part.part_pct
        })

    # Calculer dépenses communes (sa part)
    depenses_communes = _calcul_depenses_communes(id, parts)

    # Dépenses personnelles
    depenses_perso = DepenseProprietaire.query.filter_by(
        proprietaire_id=id, type_depense='personnelle'
    ).order_by(DepenseProprietaire.date_depense.desc()).all()
    total_depenses_perso = sum(float(d.montant_tnd) for d in depenses_perso)

    # Revenus (sa part)
    revenus_parts = _calcul_revenus_parts(id, parts)

    # Totaux
    total_depenses = depenses_communes + total_depenses_perso
    total_revenus = revenus_parts
    benefice = total_revenus - total_depenses

    return render_template('proprietaires/dashboard.html',
                           prop=prop,
                           parts=parts,
                           biens=biens,
                           depenses_communes=depenses_communes,
                           depenses_perso=depenses_perso,
                           total_depenses_perso=total_depenses_perso,
                           revenus_parts=revenus_parts,
                           total_depenses=total_depenses,
                           total_revenus=total_revenus,
                           benefice=benefice)


def _calcul_depenses_communes(proprietaire_id, parts):
    """Calcule la part des dépenses communes pour un propriétaire."""
    total = 0.0

    for part in parts:
        pct = part.part_pct / 100.0

        if part.type_bien == 'parcelle':
            # Dépenses liées à cette parcelle
            deps = Expense.query.filter_by(parcelle_id=part.bien_id).all()
            total += sum(float(d.montant_tnd) for d in deps) * pct

        elif part.type_bien == 'animal':
            # Coûts soins + alimentation de cet animal
            soins = AnimalSoin.query.filter_by(animal_id=part.bien_id).all()
            alims = Alimentation.query.filter_by(animal_id=part.bien_id).all()
            total += sum(float(s.cout_tnd or 0) for s in soins) * pct
            total += sum(float(a.cout_tnd or 0) for a in alims) * pct

        elif part.type_bien == 'olivier':
            # Traitements de cet olivier
            traitements = TraitementOlivier.query.filter_by(olivier_id=part.bien_id).all()
            total += sum(float(t.cout_tnd or 0) for t in traitements) * pct

        elif part.type_bien == 'materiel':
            # Coûts matériel
            couts = CoutMateriel.query.filter_by(materiel_id=part.bien_id).all()
            total += sum(float(c.montant_tnd) for c in couts) * pct

    return total


def _calcul_revenus_parts(proprietaire_id, parts):
    """Calcule la part des revenus pour un propriétaire."""
    total = 0.0

    for part in parts:
        pct = part.part_pct / 100.0

        if part.type_bien == 'parcelle':
            # Revenus des cultures de cette parcelle
            from sqlalchemy import text
            plot = db.session.get(Plot, part.bien_id)
            if plot:
                for crop in plot.crops:
                    revs = Revenue.query.filter_by(culture_id=crop.id).all()
                    total += sum(float(r.revenu_total_tnd) for r in revs) * pct

        elif part.type_bien == 'animal':
            prods = AnimalProduction.query.filter_by(animal_id=part.bien_id).all()
            total += sum(float(p.revenu_total or 0) for p in prods) * pct

        elif part.type_bien == 'olivier':
            prods = ProductionOlive.query.filter_by(olivier_id=part.bien_id).all()
            total += sum(float(p.quantite_huile or 0) * float(
                StockMoulin.query.filter_by(variete=db.session.get(Olivier, part.bien_id).variete if db.session.get(Olivier, part.bien_id) else None).first().prix_vente_litre or 0
            ) for p in prods) * pct

    return total


# ========== GESTION DES PARTS ==========

@app.route('/proprietaires/parts/add', methods=['GET', 'POST'])
@login_required
@manager_required
def add_part_proprietaire():
    proprietaires_list = Proprietaire.query.order_by(Proprietaire.nom).all()
    plots_list = Plot.query.all()
    animals_list = Animal.query.filter_by(statut='actif').all()
    oliviers_list = Olivier.query.all()
    materiels_list = Materiel.query.all()

    if request.method == 'POST':
        try:
            type_bien = request.form.get('type_bien')
            bien_id = int(request.form.get('bien_id'))
            proprietaire_id = int(request.form.get('proprietaire_id'))
            part_pct = float(request.form.get('part_pct'))

            # Vérifier que le total des parts ne dépasse pas 100%
            parts_existantes = PartProprietaire.query.filter_by(
                type_bien=type_bien, bien_id=bien_id
            ).all()
            total_existant = sum(p.part_pct for p in parts_existantes)

            if total_existant + part_pct > 100:
                flash(f'Erreur: Total des parts dépasse 100% (actuel: {total_existant}%)', 'danger')
                return render_template('proprietaires/add_part.html',
                                       proprietaires=proprietaires_list, plots=plots_list,
                                       animals=animals_list, oliviers=oliviers_list,
                                       materiels=materiels_list)

            # Vérifier si ce propriétaire a déjà une part sur ce bien
            existing = PartProprietaire.query.filter_by(
                proprietaire_id=proprietaire_id, type_bien=type_bien, bien_id=bien_id
            ).first()

            if existing:
                existing.part_pct = part_pct
                flash('Part mise à jour!', 'success')
            else:
                part = PartProprietaire(
                    proprietaire_id=proprietaire_id,
                    type_bien=type_bien,
                    bien_id=bien_id,
                    part_pct=part_pct
                )
                db.session.add(part)
                flash('Part ajoutée avec succès!', 'success')

            db.session.commit()
            return redirect(url_for('proprietaires'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')

    return render_template('proprietaires/add_part.html',
                           proprietaires=proprietaires_list, plots=plots_list,
                           animals=animals_list, oliviers=oliviers_list,
                           materiels=materiels_list)


@app.route('/proprietaires/parts/delete/<int:id>', methods=['POST'])
@login_required
@manager_required
def delete_part_proprietaire(id):
    part = db.get_or_404(PartProprietaire, id)
    try:
        db.session.delete(part)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== DEPENSES PERSONNELLES ==========

@app.route('/proprietaires/<int:id>/depenses', methods=['GET', 'POST'])
@login_required
@manager_required
def depenses_proprietaire(id):
    prop = db.get_or_404(Proprietaire, id)
    categories = ['Semences', 'Engrais', 'Eau', 'Carburant', 'Salaires',
                  'Veterinaire', 'Nourriture animale', 'Materiel', 'Autre']

    if request.method == 'POST':
        try:
            facture_fichier = save_facture(request.files.get('facture'))
            dep = DepenseProprietaire(
                proprietaire_id=id,
                categorie=request.form.get('categorie'),
                montant_tnd=float(request.form.get('montant_tnd')),
                date_depense=datetime.strptime(request.form.get('date_depense'), '%Y-%m-%d').date(),
                description=request.form.get('description'),
                type_depense=request.form.get('type_depense', 'personnelle'),
                bien_type=request.form.get('bien_type') or None,
                bien_id=int(request.form.get('bien_id')) if request.form.get('bien_id') else None,
                facture_fichier=facture_fichier,
                notes=request.form.get('notes')
            )
            db.session.add(dep)
            db.session.commit()
            flash('Dépense enregistrée!', 'success')
            return redirect(url_for('proprietaire_dashboard', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')

    depenses = DepenseProprietaire.query.filter_by(
        proprietaire_id=id
    ).order_by(DepenseProprietaire.date_depense.desc()).all()

    return render_template('proprietaires/depenses.html',
                           prop=prop, depenses=depenses,
                           categories=categories, now=datetime.now())


# ========== RAPPORT GLOBAL TOUS PROPRIETAIRES ==========

@app.route('/proprietaires/rapport')
@login_required
def rapport_proprietaires():
    proprietaires_list = Proprietaire.query.order_by(Proprietaire.nom).all()
    rapport = []

    for prop in proprietaires_list:
        parts = PartProprietaire.query.filter_by(proprietaire_id=prop.id).all()
        depenses_communes = _calcul_depenses_communes(prop.id, parts)
        revenus = _calcul_revenus_parts(prop.id, parts)

        depenses_perso = DepenseProprietaire.query.filter_by(proprietaire_id=prop.id).all()
        total_perso = sum(float(d.montant_tnd) for d in depenses_perso)

        total_depenses = depenses_communes + total_perso
        benefice = revenus - total_depenses

        rapport.append({
            'proprietaire': prop,
            'nb_biens': len(parts),
            'depenses_communes': depenses_communes,
            'depenses_perso': total_perso,
            'total_depenses': total_depenses,
            'revenus': revenus,
            'benefice': benefice
        })

    return render_template('proprietaires/rapport.html', rapport=rapport)

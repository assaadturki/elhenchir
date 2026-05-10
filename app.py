# -*- coding: utf-8 -*-
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
from sqlalchemy import func
import json
import bcrypt
import os

from config import Config
from models import db, User, Plot, Crop, Expense, Revenue, Inventory, InventoryMovement
from models import Employee, Attendance, Harvest, Notification
from models import AnimalType, Animal, AnimalSoin, AnimalProduction, Alimentation

# ========== CREATION DE L'APPLICATION ==========
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ========== MODELES OLIVIERS ==========
class Olivier(db.Model):
    __tablename__ = 'oliviers'
    id = db.Column(db.Integer, primary_key=True)
    parcelle_id = db.Column(db.Integer, db.ForeignKey('plots.id'), nullable=False)
    numero_arbre = db.Column(db.String(50), unique=True)
    variete = db.Column(db.String(100))
    age = db.Column(db.Integer)
    date_plantation = db.Column(db.Date)
    statut = db.Column(db.String(50), default='actif')
    etat_sante = db.Column(db.String(50))
    notes = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    
    productions = db.relationship('ProductionOlive', backref='olivier', lazy=True, cascade='all, delete-orphan')
    traitements = db.relationship('TraitementOlivier', backref='olivier', lazy=True, cascade='all, delete-orphan')

class ProductionOlive(db.Model):
    __tablename__ = 'production_olives'
    id = db.Column(db.Integer, primary_key=True)
    olivier_id = db.Column(db.Integer, db.ForeignKey('oliviers.id'), nullable=False)
    annee = db.Column(db.Integer, nullable=False)
    quantite_olives = db.Column(db.Float, nullable=False)
    taux_hutile = db.Column(db.Float)
    quantite_huile = db.Column(db.Float)
    qualite_huile = db.Column(db.String(50))
    acidite = db.Column(db.Float)
    date_recolte = db.Column(db.Date)
    notes = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

class TraitementOlivier(db.Model):
    __tablename__ = 'traitements_oliviers'
    id = db.Column(db.Integer, primary_key=True)
    olivier_id = db.Column(db.Integer, db.ForeignKey('oliviers.id'), nullable=False)
    date_traitement = db.Column(db.Date, nullable=False)
    type_traitement = db.Column(db.String(100))
    description = db.Column(db.Text)
    produits_utilises = db.Column(db.String(200))
    cout_tnd = db.Column(db.Numeric(10, 2))
    notes = db.Column(db.Text)

class StockMoulin(db.Model):
    __tablename__ = 'stock_moulin'
    id = db.Column(db.Integer, primary_key=True)
    campagne = db.Column(db.String(20))
    variete = db.Column(db.String(100))
    quantite_litres = db.Column(db.Float, nullable=False)
    qualite = db.Column(db.String(50))
    prix_vente_litre = db.Column(db.Numeric(10, 3))
    date_stock = db.Column(db.Date, default=datetime.utcnow)
    date_peremption = db.Column(db.Date)
    notes = db.Column(db.Text)

# ========== LOAD USER ==========
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ========== CREATION DES TABLES ==========
with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='admin@farm.com').first():
        admin = User(nom='Administrateur', email='admin@farm.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin cree: admin@farm.com / admin123")

# ========== ROUTES PRINCIPALES ==========
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Connexion reussie!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou mot de passe incorrect', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Deconnexion reussie', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    today = datetime.now().date()
    first_day = today.replace(day=1)
    
    monthly_expenses = db.session.query(func.sum(Expense.montant_tnd)).filter(
        Expense.date_depense >= first_day
    ).scalar() or 0
    
    monthly_revenues = db.session.query(func.sum(Revenue.revenu_total_tnd)).filter(
        Revenue.date_vente >= first_day
    ).scalar() or 0
    
    monthly_profit = float(monthly_revenues) - float(monthly_expenses)
    active_crops = Crop.query.filter(Crop.statut.in_(['planifie', 'en_cours'])).count()
    low_stock = Inventory.query.filter(Inventory.quantite <= Inventory.seuil_alerte).all()
    
    return render_template('dashboard.html',
                         monthly_expenses=float(monthly_expenses),
                         monthly_revenues=float(monthly_revenues),
                         monthly_profit=monthly_profit,
                         active_crops=active_crops,
                         low_stock=low_stock)

# ========== PARCELLES ==========
@app.route('/plots')
@login_required
def plots():
    all_plots = Plot.query.all()
    return render_template('plots/index.html', plots=all_plots)

@app.route('/plots/create', methods=['GET', 'POST'])
@login_required
def create_plot():
    if request.method == 'POST':
        plot = Plot(
            nom=request.form.get('nom'),
            superficie=float(request.form.get('superficie')),
            localisation=request.form.get('localisation'),
            type_sol=request.form.get('type_sol'),
            irrigation=request.form.get('irrigation'),
            statut=request.form.get('statut')
        )
        db.session.add(plot)
        db.session.commit()
        flash('Parcelle ajoutee avec succes!', 'success')
        return redirect(url_for('plots'))
    return render_template('plots/create.html')

@app.route('/plots/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_plot(id):
    plot = Plot.query.get_or_404(id)
    if request.method == 'POST':
        plot.nom = request.form.get('nom')
        plot.superficie = float(request.form.get('superficie'))
        plot.localisation = request.form.get('localisation')
        plot.type_sol = request.form.get('type_sol')
        plot.irrigation = request.form.get('irrigation')
        plot.statut = request.form.get('statut')
        db.session.commit()
        flash('Parcelle modifiee avec succes!', 'success')
        return redirect(url_for('plots'))
    return render_template('plots/edit.html', plot=plot)

@app.route('/plots/delete/<int:id>')
@login_required
def delete_plot(id):
    plot = Plot.query.get_or_404(id)
    db.session.delete(plot)
    db.session.commit()
    flash('Parcelle supprimee avec succes!', 'success')
    return redirect(url_for('plots'))

# ========== CULTURES ==========
@app.route('/crops')
@login_required
def crops():
    all_crops = Crop.query.all()
    return render_template('crops/index.html', crops=all_crops)

@app.route('/crops/create', methods=['GET', 'POST'])
@login_required
def create_crop():
    plots = Plot.query.all()
    if request.method == 'POST':
        crop = Crop(
            parcelle_id=int(request.form.get('parcelle_id')),
            nom_culture=request.form.get('nom_culture'),
            variete=request.form.get('variete'),
            date_semis=datetime.strptime(request.form.get('date_semis'), '%Y-%m-%d').date(),
            date_recolte_prevue=datetime.strptime(request.form.get('date_recolte_prevue'), '%Y-%m-%d').date() if request.form.get('date_recolte_prevue') else None,
            quantite_estimee=float(request.form.get('quantite_estimee')) if request.form.get('quantite_estimee') else None,
            unite=request.form.get('unite'),
            notes=request.form.get('notes')
        )
        db.session.add(crop)
        db.session.commit()
        flash('Culture ajoutee avec succes!', 'success')
        return redirect(url_for('crops'))
    return render_template('crops/create.html', plots=plots)

@app.route('/crops/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_crop(id):
    crop = Crop.query.get_or_404(id)
    plots = Plot.query.all()
    if request.method == 'POST':
        crop.parcelle_id = int(request.form.get('parcelle_id'))
        crop.nom_culture = request.form.get('nom_culture')
        crop.variete = request.form.get('variete')
        crop.date_semis = datetime.strptime(request.form.get('date_semis'), '%Y-%m-%d').date()
        crop.date_recolte_prevue = datetime.strptime(request.form.get('date_recolte_prevue'), '%Y-%m-%d').date() if request.form.get('date_recolte_prevue') else None
        crop.quantite_estimee = float(request.form.get('quantite_estimee')) if request.form.get('quantite_estimee') else None
        crop.unite = request.form.get('unite')
        crop.statut = request.form.get('statut')
        crop.notes = request.form.get('notes')
        db.session.commit()
        flash('Culture modifiee avec succes!', 'success')
        return redirect(url_for('crops'))
    return render_template('crops/edit.html', crop=crop, plots=plots)

# ========== DEPENSES ==========
@app.route('/expenses')
@login_required
def expenses():
    all_expenses = Expense.query.order_by(Expense.date_depense.desc()).all()
    return render_template('expenses/index.html', expenses=all_expenses)

@app.route('/expenses/create', methods=['GET', 'POST'])
@login_required
def create_expense():
    plots = Plot.query.all()
    categories = ['Semences', 'Engrais', 'Eau', 'Carburant', 'Salaires', 
                  'Transport', 'Reparation materiel', 'Electricite', 
                  'Produits veterinaires', 'Nourriture animale', 'Loyer', 'Assurances', 'Autre']
    
    if request.method == 'POST':
        expense = Expense(
            categorie=request.form.get('categorie'),
            montant_tnd=float(request.form.get('montant_tnd')),
            date_depense=datetime.strptime(request.form.get('date_depense'), '%Y-%m-%d').date(),
            description=request.form.get('description'),
            parcelle_id=int(request.form.get('parcelle_id')) if request.form.get('parcelle_id') else None,
            fournisseur=request.form.get('fournisseur'),
            reference=request.form.get('reference')
        )
        db.session.add(expense)
        db.session.commit()
        flash('Depense ajoutee avec succes!', 'success')
        return redirect(url_for('expenses'))
    
    return render_template('expenses/create.html', plots=plots, categories=categories, now=datetime.now())

# ========== REVENUS ==========
@app.route('/revenues')
@login_required
def revenues():
    all_revenues = Revenue.query.order_by(Revenue.date_vente.desc()).all()
    return render_template('revenues/index.html', revenues=all_revenues)

@app.route('/revenues/create', methods=['GET', 'POST'])
@login_required
def create_revenue():
    crops = Crop.query.all()
    
    if request.method == 'POST':
        quantite = float(request.form.get('quantite_vendue'))
        prix = float(request.form.get('prix_unitaire_tnd'))
        total = quantite * prix
        
        revenue = Revenue(
            culture_id=int(request.form.get('culture_id')),
            quantite_vendue=quantite,
            prix_unitaire_tnd=prix,
            revenu_total_tnd=total,
            date_vente=datetime.strptime(request.form.get('date_vente'), '%Y-%m-%d').date(),
            client=request.form.get('client'),
            facture_numero=request.form.get('facture_numero'),
            notes=request.form.get('notes')
        )
        db.session.add(revenue)
        db.session.commit()
        flash('Vente enregistree avec succes!', 'success')
        return redirect(url_for('revenues'))
    
    return render_template('revenues/create.html', crops=crops, now=datetime.now())

@app.route('/revenues/delete/<int:id>', methods=['POST'])
@login_required
def delete_revenue(id):
    revenue = Revenue.query.get_or_404(id)
    db.session.delete(revenue)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/revenues/delete/all', methods=['POST'])
@login_required
def delete_all_revenues():
    # Supprimer uniquement les revenus de test (sans culture associée ou avec client "Vente huile d'olive")
    Revenu.query.filter(
        (Revenue.culture_id == None) | 
        (Revenue.client == 'Vente huile d\'olive') |
        (Revenue.revenu_total_tnd == 0)
    ).delete()
    db.session.commit()
    return jsonify({'success': True})

# ========== STOCK ==========
@app.route('/inventory')
@login_required
def inventory():
    items = Inventory.query.all()
    return render_template('inventory/index.html', items=items)

@app.route('/inventory/create', methods=['GET', 'POST'])
@login_required
def create_inventory():
    categories = ['Engrais', 'Semences', 'Produits chimiques', 'Nourriture animale', 'Pieces materiel', 'Outils', 'Autre']
    
    if request.method == 'POST':
        item = Inventory(
            produit=request.form.get('produit'),
            categorie=request.form.get('categorie'),
            quantite=float(request.form.get('quantite')),
            unite=request.form.get('unite'),
            seuil_alerte=float(request.form.get('seuil_alerte')) if request.form.get('seuil_alerte') else 10,
            prix_unitaire=float(request.form.get('prix_unitaire')) if request.form.get('prix_unitaire') else None,
            emplacement=request.form.get('emplacement'),
            fournisseur=request.form.get('fournisseur')
        )
        db.session.add(item)
        db.session.commit()
        
        movement = InventoryMovement(
            produit_id=item.id,
            type_mouvement='entree',
            quantite=float(request.form.get('quantite')),
            raison='Creation initiale du stock',
            utilisateur_id=current_user.id
        )
        db.session.add(movement)
        db.session.commit()
        
        flash('Produit ajoute au stock avec succes!', 'success')
        return redirect(url_for('inventory'))
    
    return render_template('inventory/create.html', categories=categories)

@app.route('/inventory/movement/<int:id>', methods=['POST'])
@login_required
def add_movement(id):
    item = Inventory.query.get_or_404(id)
    type_mvt = request.form.get('type_mouvement')
    quantite = float(request.form.get('quantite'))
    raison = request.form.get('raison')
    
    if type_mvt == 'sortie' and quantite > item.quantite:
        flash('Quantite insuffisante en stock!', 'danger')
        return redirect(url_for('inventory'))
    
    if type_mvt == 'entree':
        item.quantite += quantite
    else:
        item.quantite -= quantite
    
    movement = InventoryMovement(
        produit_id=item.id,
        type_mouvement=type_mvt,
        quantite=quantite,
        raison=raison,
        utilisateur_id=current_user.id
    )
    db.session.add(movement)
    db.session.commit()
    
    flash('Mouvement de stock enregistre avec succes!', 'success')
    return redirect(url_for('inventory'))

# ========== EMPLOYES ==========
@app.route('/employees')
@login_required
def employees():
    all_employees = Employee.query.all()
    return render_template('employees/index.html', employees=all_employees)

@app.route('/employees/create', methods=['GET', 'POST'])
@login_required
def create_employee():
    if request.method == 'POST':
        employee = Employee(
            nom=request.form.get('nom'),
            prenom=request.form.get('prenom'),
            telephone=request.form.get('telephone'),
            email=request.form.get('email'),
            poste=request.form.get('poste'),
            salaire_tnd=float(request.form.get('salaire_tnd')) if request.form.get('salaire_tnd') else None,
            date_embauche=datetime.strptime(request.form.get('date_embauche'), '%Y-%m-%d').date() if request.form.get('date_embauche') else None,
            date_naissance=datetime.strptime(request.form.get('date_naissance'), '%Y-%m-%d').date() if request.form.get('date_naissance') else None,
            adresse=request.form.get('adresse'),
            cin=request.form.get('cin'),
            notes=request.form.get('notes')
        )
        db.session.add(employee)
        db.session.commit()
        flash('Employe ajoute avec succes!', 'success')
        return redirect(url_for('employees'))
    return render_template('employees/create.html')

@app.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    if request.method == 'POST':
        employee.nom = request.form.get('nom')
        employee.prenom = request.form.get('prenom')
        employee.telephone = request.form.get('telephone')
        employee.email = request.form.get('email')
        employee.poste = request.form.get('poste')
        employee.salaire_tnd = float(request.form.get('salaire_tnd')) if request.form.get('salaire_tnd') else None
        employee.date_embauche = datetime.strptime(request.form.get('date_embauche'), '%Y-%m-%d').date() if request.form.get('date_embauche') else None
        employee.date_naissance = datetime.strptime(request.form.get('date_naissance'), '%Y-%m-%d').date() if request.form.get('date_naissance') else None
        employee.adresse = request.form.get('adresse')
        employee.cin = request.form.get('cin')
        employee.statut = request.form.get('statut')
        employee.notes = request.form.get('notes')
        db.session.commit()
        flash('Employe modifie avec succes!', 'success')
        return redirect(url_for('employees'))
    return render_template('employees/edit.html', employee=employee)

@app.route('/employees/attendance/<int:id>', methods=['GET', 'POST'])
@login_required
def manage_attendance(id):
    employee = Employee.query.get_or_404(id)
    if request.method == 'POST':
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        arrivee = datetime.strptime(request.form.get('heure_arrivee'), '%H:%M').time() if request.form.get('heure_arrivee') else None
        depart = datetime.strptime(request.form.get('heure_depart'), '%H:%M').time() if request.form.get('heure_depart') else None
        
        heures = 0
        if arrivee and depart:
            delta = datetime.combine(date, depart) - datetime.combine(date, arrivee)
            heures = delta.total_seconds() / 3600
        
        attendance = Attendance(
            employe_id=employee.id,
            date=date,
            heure_arrivee=arrivee,
            heure_depart=depart,
            heures_travaillees=heures,
            statut=request.form.get('statut'),
            notes=request.form.get('notes')
        )
        db.session.add(attendance)
        db.session.commit()
        flash('Presence enregistree avec succes!', 'success')
        return redirect(url_for('employees'))
    return render_template('employees/attendance.html', employee=employee)

# ========== RECOLTES ==========
@app.route('/harvests')
@login_required
def harvests():
    all_harvests = Harvest.query.order_by(Harvest.date_recolte.desc()).all()
    return render_template('harvests/index.html', harvests=all_harvests)

@app.route('/harvests/<int:id>')
@login_required
def harvests_detail(id):
    harvest = Harvest.query.get_or_404(id)
    return render_template('harvests/detail.html', harvest=harvest)

@app.route('/harvests/create/<int:crop_id>', methods=['GET', 'POST'])
@login_required
def harvests_create(crop_id):
    crop = Crop.query.get_or_404(crop_id)
    
    if request.method == 'POST':
        date_recolte = datetime.strptime(request.form.get('date_recolte'), '%Y-%m-%d').date()
        quantite = float(request.form.get('quantite_recoltee'))
        pertes = float(request.form.get('pertes')) if request.form.get('pertes') else 0
        
        harvest = Harvest(
            culture_id=crop.id,
            date_recolte=date_recolte,
            quantite_recoltee=quantite,
            unite=request.form.get('unite'),
            qualite=request.form.get('qualite'),
            pertes=pertes,
            main_doeuvre=int(request.form.get('main_doeuvre')) if request.form.get('main_doeuvre') else None,
            notes=request.form.get('notes')
        )
        db.session.add(harvest)
        
        crop.quantite_recoltee = quantite
        crop.date_recolte_reelle = date_recolte
        crop.statut = 'recolte'
        
        db.session.commit()
        flash('Recolte enregistree avec succes!', 'success')
        return redirect(url_for('crops'))
    
    qualites = ['Extra', 'Premiere', 'Deuxieme', 'Standard', 'Conservation']
    return render_template('harvests/create.html', crop=crop, now=datetime.now(), qualites=qualites)

@app.route('/harvests/delete/<int:id>', methods=['POST'])
@login_required
def harvests_delete(id):
    harvest = Harvest.query.get_or_404(id)
    db.session.delete(harvest)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/harvests/export')
@login_required
def harvests_export():
    from openpyxl import Workbook
    import os
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Recoltes"
    
    headers = ['Date recolte', 'Culture', 'Parcelle', 'Quantite', 'Unite', 'Qualite', 'Pertes (%)']
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    
    harvests = Harvest.query.all()
    for row, harvest in enumerate(harvests, 2):
        ws.cell(row=row, column=1, value=harvest.date_recolte.strftime('%d/%m/%Y'))
        ws.cell(row=row, column=2, value=harvest.crop.nom_culture if harvest.crop else '-')
        ws.cell(row=row, column=3, value=harvest.crop.plot.nom if harvest.crop and harvest.crop.plot else '-')
        ws.cell(row=row, column=4, value=float(harvest.quantite_recoltee))
        ws.cell(row=row, column=5, value=harvest.unite)
        ws.cell(row=row, column=6, value=harvest.qualite or '-')
        ws.cell(row=row, column=7, value=float(harvest.pertes))
    
    filename = f"recoltes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join('exports', filename)
    wb.save(filepath)
    
    return jsonify({'success': True, 'filename': filename})

# ========== ELEVAGE - DASHBOARD ==========
@app.route('/livestock/dashboard')
@login_required
def livestock_dashboard():
    total_animaux = Animal.query.count()
    animaux_actifs = Animal.query.filter_by(statut='actif').count()
    animaux_vendus = Animal.query.filter_by(statut='vendu').count()
    production_mensuelle = db.session.query(func.sum(AnimalProduction.revenu_total)).filter(
        AnimalProduction.date_production >= datetime.now().replace(day=1)
    ).scalar() or 0
    soins_recents = AnimalSoin.query.order_by(AnimalSoin.date_soin.desc()).limit(10).all()
    
    return render_template('livestock/dashboard.html',
                         total_animaux=total_animaux,
                         animaux_actifs=animaux_actifs,
                         animaux_vendus=animaux_vendus,
                         production_mensuelle=float(production_mensuelle),
                         soins_recents=soins_recents)

# ========== ELEVAGE - TYPES ==========
@app.route('/livestock/types')
@login_required
def animal_types():
    types = AnimalType.query.all()
    return render_template('livestock/types.html', types=types)

@app.route('/livestock/types/create', methods=['GET', 'POST'])
@login_required
def create_animal_type():
    if request.method == 'POST':
        animal_type = AnimalType(
            nom=request.form.get('nom'),
            categorie=request.form.get('categorie'),
            description=request.form.get('description')
        )
        db.session.add(animal_type)
        db.session.commit()
        flash('Type d\'animal ajoute avec succes!', 'success')
        return redirect(url_for('animal_types'))
    return render_template('livestock/create_type.html')

# ========== ELEVAGE - ANIMAUX ==========
@app.route('/livestock/animals')
@login_required
def animals():
    animals = Animal.query.all()
    return render_template('livestock/animals.html', animals=animals)

@app.route('/livestock/animals/create', methods=['GET', 'POST'])
@login_required
def create_animal():
    types = AnimalType.query.all()
    plots = Plot.query.all()
    
    if request.method == 'POST':
        animal = Animal(
            type_id=int(request.form.get('type_id')),
            numero_identification=request.form.get('numero_identification'),
            nom=request.form.get('nom'),
            sexe=request.form.get('sexe'),
            date_naissance=datetime.strptime(request.form.get('date_naissance'), '%Y-%m-%d').date() if request.form.get('date_naissance') else None,
            race=request.form.get('race'),
            couleur=request.form.get('couleur'),
            poids_naissance=float(request.form.get('poids_naissance')) if request.form.get('poids_naissance') else None,
            poids_actuel=float(request.form.get('poids_actuel')) if request.form.get('poids_actuel') else None,
            prix_achat=float(request.form.get('prix_achat')) if request.form.get('prix_achat') else None,
            date_achat=datetime.strptime(request.form.get('date_achat'), '%Y-%m-%d').date() if request.form.get('date_achat') else None,
            provenance=request.form.get('provenance'),
            parcelle_id=int(request.form.get('parcelle_id')) if request.form.get('parcelle_id') else None,
            notes=request.form.get('notes')
        )
        db.session.add(animal)
        db.session.commit()
        flash('Animal ajoute avec succes!', 'success')
        return redirect(url_for('animals'))
    
    return render_template('livestock/create_animal.html', types=types, plots=plots)

@app.route('/livestock/animals/<int:id>')
@login_required
def animal_detail(id):
    animal = Animal.query.get_or_404(id)
    soins = AnimalSoin.query.filter_by(animal_id=id).order_by(AnimalSoin.date_soin.desc()).all()
    productions = AnimalProduction.query.filter_by(animal_id=id).order_by(AnimalProduction.date_production.desc()).all()
    return render_template('livestock/animal_detail.html', animal=animal, soins=soins, productions=productions, now=datetime.now())

@app.route('/livestock/animals/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_animal(id):
    animal = Animal.query.get_or_404(id)
    types = AnimalType.query.all()
    plots = Plot.query.all()
    
    if request.method == 'POST':
        animal.type_id = int(request.form.get('type_id'))
        animal.numero_identification = request.form.get('numero_identification')
        animal.nom = request.form.get('nom')
        animal.sexe = request.form.get('sexe')
        animal.date_naissance = datetime.strptime(request.form.get('date_naissance'), '%Y-%m-%d').date() if request.form.get('date_naissance') else None
        animal.race = request.form.get('race')
        animal.couleur = request.form.get('couleur')
        animal.poids_naissance = float(request.form.get('poids_naissance')) if request.form.get('poids_naissance') else None
        animal.poids_actuel = float(request.form.get('poids_actuel')) if request.form.get('poids_actuel') else None
        animal.prix_achat = float(request.form.get('prix_achat')) if request.form.get('prix_achat') else None
        animal.date_achat = datetime.strptime(request.form.get('date_achat'), '%Y-%m-%d').date() if request.form.get('date_achat') else None
        animal.provenance = request.form.get('provenance')
        animal.parcelle_id = int(request.form.get('parcelle_id')) if request.form.get('parcelle_id') else None
        animal.statut = request.form.get('statut')
        animal.notes = request.form.get('notes')
        db.session.commit()
        flash('Animal modifie avec succes!', 'success')
        return redirect(url_for('animals'))
    
    return render_template('livestock/edit_animal.html', animal=animal, types=types, plots=plots, now=datetime.now())

# ========== ELEVAGE - SOINS ==========
@app.route('/livestock/soins/create/<int:animal_id>', methods=['GET', 'POST'])
@login_required
def create_soin(animal_id):
    animal = Animal.query.get_or_404(animal_id)
    
    if request.method == 'POST':
        soin = AnimalSoin(
            animal_id=animal_id,
            date_soin=datetime.strptime(request.form.get('date_soin'), '%Y-%m-%d').date(),
            type_soin=request.form.get('type_soin'),
            description=request.form.get('description'),
            veterinaire=request.form.get('veterinaire'),
            cout_tnd=float(request.form.get('cout_tnd')) if request.form.get('cout_tnd') else None,
            produits_utilises=request.form.get('produits_utilises'),
            prochain_rappel=datetime.strptime(request.form.get('prochain_rappel'), '%Y-%m-%d').date() if request.form.get('prochain_rappel') else None,
            notes=request.form.get('notes')
        )
        db.session.add(soin)
        db.session.commit()
        flash('Soin enregistre avec succes!', 'success')
        return redirect(url_for('animal_detail', id=animal_id))
    
    types_soin = ['Vaccination', 'Traitement', 'Consultation', 'Operation', 'Controle sanitaire']
    return render_template('livestock/create_soin.html', animal=animal, types_soin=types_soin, now=datetime.now())

# ========== ELEVAGE - PRODUCTIONS ==========
@app.route('/livestock/productions/create/<int:animal_id>', methods=['GET', 'POST'])
@login_required
def create_production(animal_id):
    animal = Animal.query.get_or_404(animal_id)
    
    if request.method == 'POST':
        quantite = float(request.form.get('quantite'))
        prix = float(request.form.get('prix_vente_unitaire')) if request.form.get('prix_vente_unitaire') else 0
        revenu = quantite * prix
        
        production = AnimalProduction(
            animal_id=animal_id,
            date_production=datetime.strptime(request.form.get('date_production'), '%Y-%m-%d').date(),
            type_produit=request.form.get('type_produit'),
            quantite=quantite,
            unite=request.form.get('unite'),
            prix_vente_unitaire=prix,
            revenu_total=revenu,
            notes=request.form.get('notes')
        )
        db.session.add(production)
        db.session.commit()
        
        if revenu > 0:
            revenue = Revenue(
                culture_id=None,
                quantite_vendue=quantite,
                prix_unitaire_tnd=prix,
                revenu_total_tnd=revenu,
                date_vente=datetime.now().date(),
                client='Vente directe',
                notes=f'Production de {animal.nom or animal.numero_identification}: {request.form.get("type_produit")}'
            )
            db.session.add(revenue)
            db.session.commit()
        
        flash(f'Production enregistree! Revenu: {revenu:.3f} TND', 'success')
        return redirect(url_for('animal_detail', id=animal_id))
    
    types_produit = ['Lait', 'Oeufs', 'Laine', 'Miel', 'Cuir', 'Viande']
    unites = ['L', 'kg', 'pieces', 'g']
    return render_template('livestock/create_production.html', animal=animal, types_produit=types_produit, unites=unites, now=datetime.now())

# ========== ELEVAGE - ALIMENTATION ==========
@app.route('/livestock/alimentations')
@login_required
def alimentations():
    alimentations = Alimentation.query.order_by(Alimentation.date_alimentation.desc()).all()
    return render_template('livestock/alimentations.html', alimentations=alimentations)

@app.route('/livestock/alimentations/create', methods=['GET', 'POST'])
@login_required
def create_alimentation():
    from datetime import datetime
    animaux = Animal.query.filter_by(statut='actif').all()
    
    if request.method == 'POST':
        try:
            animal_id = int(request.form.get('animal_id'))
            animal = Animal.query.get(animal_id)
            
            if not animal:
                flash('Animal non trouve!', 'danger')
                return redirect(url_for('alimentations'))
            
            date_alimentation = datetime.strptime(request.form.get('date_alimentation'), '%Y-%m-%d').date() if request.form.get('date_alimentation') else datetime.now().date()
            cout_tnd = float(request.form.get('cout_tnd')) if request.form.get('cout_tnd') else 0
            
            alimentation = Alimentation(
                animal_id=animal_id,
                date_alimentation=date_alimentation,
                type_nourriture=request.form.get('type_nourriture'),
                quantite=float(request.form.get('quantite')),
                unite=request.form.get('unite'),
                cout_tnd=cout_tnd,
                notes=request.form.get('notes')
            )
            db.session.add(alimentation)
            
            # Ajouter automatiquement la dépense
            if cout_tnd > 0:
                expense = Expense(
                    categorie='Nourriture animale',
                    montant_tnd=cout_tnd,
                    date_depense=date_alimentation,
                    description=f'Alimentation: {request.form.get("type_nourriture")} - {animal.nom or animal.numero_identification or "Animal"}',
                    fournisseur='Achats alimentation'
                )
                db.session.add(expense)
            
            db.session.commit()
            flash(f'Alimentation enregistree avec succes! Cout: {cout_tnd:.3f} TND', 'success')
            return redirect(url_for('alimentations'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
            return redirect(url_for('create_alimentation'))
    
    return render_template('livestock/create_alimentation.html', animaux=animaux, now=datetime.now())

# ========== OLIVIERS ==========
@app.route('/oliviers')
@login_required
def oliviers():
    oliviers = Olivier.query.all()
    return render_template('oliviers/index.html', oliviers=oliviers)

@app.route('/oliviers/create', methods=['GET', 'POST'])
@login_required
def create_olivier():
    parcelles = Plot.query.all()
    varietes = ['Chemlali', 'Chetoui', 'Zarrazi', 'Oueslati', 'Sayali', 'Autre']
    
    if request.method == 'POST':
        olivier = Olivier(
            parcelle_id=int(request.form.get('parcelle_id')),
            numero_arbre=request.form.get('numero_arbre'),
            variete=request.form.get('variete'),
            age=int(request.form.get('age')) if request.form.get('age') else None,
            date_plantation=datetime.strptime(request.form.get('date_plantation'), '%Y-%m-%d').date() if request.form.get('date_plantation') else None,
            etat_sante=request.form.get('etat_sante'),
            notes=request.form.get('notes')
        )
        db.session.add(olivier)
        db.session.commit()
        flash('Olivier ajoute avec succes!', 'success')
        return redirect(url_for('oliviers'))
    
    return render_template('oliviers/create.html', parcelles=parcelles, varietes=varietes)

@app.route('/oliviers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_olivier(id):
    from datetime import datetime
    olivier = Olivier.query.get_or_404(id)
    parcelles = Plot.query.all()
    varietes = ['Chemlali', 'Chetoui', 'Zarrazi', 'Oueslati', 'Sayali', 'Autre']
    etats_sante = ['Excellent', 'Bon', 'Moyen', 'Mauvais']
    
    if request.method == 'POST':
        olivier.parcelle_id = int(request.form.get('parcelle_id'))
        olivier.numero_arbre = request.form.get('numero_arbre')
        olivier.variete = request.form.get('variete')
        olivier.age = int(request.form.get('age')) if request.form.get('age') else None
        olivier.date_plantation = datetime.strptime(request.form.get('date_plantation'), '%Y-%m-%d').date() if request.form.get('date_plantation') else None
        olivier.statut = request.form.get('statut')
        olivier.etat_sante = request.form.get('etat_sante')
        olivier.notes = request.form.get('notes')
        db.session.commit()
        flash('Olivier modifie avec succes!', 'success')
        return redirect(url_for('oliviers'))
    
    return render_template('oliviers/edit.html', olivier=olivier, parcelles=parcelles, varietes=varietes, etats_sante=etats_sante)

@app.route('/oliviers/<int:id>')
@login_required
def olivier_detail(id):
    olivier = Olivier.query.get_or_404(id)
    productions = ProductionOlive.query.filter_by(olivier_id=id).order_by(ProductionOlive.annee.desc()).all()
    return render_template('oliviers/detail.html', olivier=olivier, productions=productions)

@app.route('/oliviers/production/add/<int:olivier_id>', methods=['GET', 'POST'])
@login_required
def add_production_olive(olivier_id):
    from datetime import datetime
    olivier = Olivier.query.get_or_404(olivier_id)
    
    if request.method == 'POST':
        quantite_olives = float(request.form.get('quantite_olives'))
        taux_hutile = float(request.form.get('taux_hutile')) if request.form.get('taux_hutile') else 0
        quantite_huile = quantite_olives * (taux_hutile / 100)
        
        production = ProductionOlive(
            olivier_id=olivier_id,
            annee=int(request.form.get('annee')),
            quantite_olives=quantite_olives,
            taux_hutile=taux_hutile,
            quantite_huile=quantite_huile,
            qualite_huile=request.form.get('qualite_huile'),
            acidite=float(request.form.get('acidite')) if request.form.get('acidite') else None,
            date_recolte=datetime.strptime(request.form.get('date_recolte'), '%Y-%m-%d').date() if request.form.get('date_recolte') else None,
            notes=request.form.get('notes')
        )
        db.session.add(production)
        
        # Ajouter automatiquement au stock d'huile
        if quantite_huile > 0:
            stock = StockMoulin(
                campagne=request.form.get('annee'),
                variete=olivier.variete,
                quantite_litres=quantite_huile,
                qualite=request.form.get('qualite_huile'),
                prix_vente_litre=float(request.form.get('prix_huile')) if request.form.get('prix_huile') else None,
                date_stock=datetime.now().date(),
                notes=f"Production de l'olivier {olivier.numero_arbre or ''}"
            )
            db.session.add(stock)
        
        db.session.commit()
        
        # Ajouter aux revenus
        if quantite_huile > 0:
            prix_huile = float(request.form.get('prix_huile')) if request.form.get('prix_huile') else 0
            revenu_total = quantite_huile * prix_huile
            
            if revenu_total > 0:
                revenue = Revenue(
                    culture_id=None,
                    quantite_vendue=quantite_huile,
                    prix_unitaire_tnd=prix_huile,
                    revenu_total_tnd=revenu_total,
                    date_vente=datetime.now().date(),
                    client=request.form.get('client') or 'Vente huile d\'olive',
                    notes=f"Huile d'olive - {olivier.variete} - Campagne {request.form.get('annee')} - {quantite_huile:.2f} L"
                )
                db.session.add(revenue)
        
        db.session.commit()
        flash(f'Production enregistree! {quantite_huile:.2f} L d\'huile', 'success')
        return redirect(url_for('olivier_detail', id=olivier_id))
    
    qualites = ['Extra vierge', 'Vierge', 'Lampante']
    return render_template('oliviers/add_production.html', olivier=olivier, qualites=qualites, now=datetime.now())

@app.route('/stock/huile')
@login_required
def stock_huile():
    stock = StockMoulin.query.order_by(StockMoulin.campagne.desc()).all()
    return render_template('oliviers/stock_huile.html', stock=stock)

@app.route('/stock/huile/add', methods=['GET', 'POST'])
@login_required
def add_stock_huile():
    from datetime import datetime
    
    if request.method == 'POST':
        stock = StockMoulin(
            campagne=request.form.get('campagne'),
            variete=request.form.get('variete'),
            quantite_litres=float(request.form.get('quantite_litres')),
            qualite=request.form.get('qualite'),
            prix_vente_litre=float(request.form.get('prix_vente_litre')) if request.form.get('prix_vente_litre') else None,
            date_stock=datetime.strptime(request.form.get('date_stock'), '%Y-%m-%d').date() if request.form.get('date_stock') else datetime.now().date(),
            notes=request.form.get('notes')
        )
        db.session.add(stock)
        db.session.commit()
        flash('Stock d\'huile ajoute avec succes!', 'success')
        return redirect(url_for('stock_huile'))
    
    now = datetime.now()
    return render_template('oliviers/add_stock_huile.html', now=now)

@app.route('/dashboard/oliveraie')
@login_required
def dashboard_oliveraie():
    total_oliviers = Olivier.query.count()
    total_actifs = Olivier.query.filter_by(statut='actif').count()
    production_totale = db.session.query(func.sum(ProductionOlive.quantite_huile)).scalar() or 0
    
    production_par_variete = db.session.query(
        Olivier.variete,
        func.sum(ProductionOlive.quantite_huile).label('total_huile')
    ).join(ProductionOlive, Olivier.id == ProductionOlive.olivier_id).group_by(Olivier.variete).all()
    
    return render_template('oliviers/dashboard.html', 
                         total_oliviers=total_oliviers,
                         total_actifs=total_actifs,
                         production_totale=float(production_totale),
                         production_par_variete=production_par_variete)

@app.route('/oliviers/delete/<int:id>', methods=['POST'])
@login_required
def delete_olivier(id):
    olivier = Olivier.query.get_or_404(id)
    try:
        db.session.delete(olivier)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== LANCEMENT ==========
if __name__ == '__main__':
    if not os.path.exists('exports'):
        os.makedirs('exports')
    app.run(debug=True, host='0.0.0.0', port=5000)
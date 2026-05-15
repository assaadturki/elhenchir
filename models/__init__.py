from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='employee')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    telephone = db.Column(db.String(20))
    adresse = db.Column(db.Text)

    def set_password(self, password):
        self.mot_de_passe = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.mot_de_passe.encode('utf-8'))


class Plot(db.Model):
    __tablename__ = 'plots'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    superficie = db.Column(db.Float, nullable=False)
    localisation = db.Column(db.String(255))
    type_sol = db.Column(db.String(100))
    irrigation = db.Column(db.String(100))
    statut = db.Column(db.String(50), default='active')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    crops = db.relationship('Crop', backref='plot', lazy=True, cascade='all, delete-orphan')
    expenses = db.relationship('Expense', backref='plot', lazy=True, cascade='all, delete-orphan')


class Crop(db.Model):
    __tablename__ = 'crops'
    id = db.Column(db.Integer, primary_key=True)
    parcelle_id = db.Column(db.Integer, db.ForeignKey('plots.id'), nullable=False)
    nom_culture = db.Column(db.String(100), nullable=False)
    variete = db.Column(db.String(100))
    date_semis = db.Column(db.Date, nullable=False)
    date_recolte_prevue = db.Column(db.Date)
    date_recolte_reelle = db.Column(db.Date)
    quantite_estimee = db.Column(db.Float)
    quantite_recoltee = db.Column(db.Float)
    unite = db.Column(db.String(20), default='kg')
    statut = db.Column(db.String(50), default='planifie')
    notes = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    revenues = db.relationship('Revenue', backref='crop', lazy=True, cascade='all, delete-orphan')
    harvests = db.relationship('Harvest', backref='crop', lazy=True, cascade='all, delete-orphan')


class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    categorie = db.Column(db.String(100), nullable=False)
    montant_tnd = db.Column(db.Numeric(10, 2), nullable=False)
    date_depense = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    parcelle_id = db.Column(db.Integer, db.ForeignKey('plots.id'))
    reference = db.Column(db.String(100))
    fournisseur = db.Column(db.String(200))
    facture_fichier = db.Column(db.String(255))  # upload facture PDF/image
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)


class Revenue(db.Model):
    __tablename__ = 'revenues'
    id = db.Column(db.Integer, primary_key=True)
    culture_id = db.Column(db.Integer, db.ForeignKey('crops.id'), nullable=True)  # nullable pour elevage/oliviers
    quantite_vendue = db.Column(db.Float, nullable=False)
    prix_unitaire_tnd = db.Column(db.Numeric(10, 3), nullable=False)
    revenu_total_tnd = db.Column(db.Numeric(10, 2), nullable=False)
    date_vente = db.Column(db.Date, nullable=False)
    client = db.Column(db.String(200))
    facture_numero = db.Column(db.String(100))
    notes = db.Column(db.Text)
    source = db.Column(db.String(50), default='culture')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)


class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    produit = db.Column(db.String(100), nullable=False)
    categorie = db.Column(db.String(50))
    quantite = db.Column(db.Float, nullable=False)
    unite = db.Column(db.String(20), default='kg')
    seuil_alerte = db.Column(db.Float, default=10)
    prix_unitaire = db.Column(db.Numeric(10, 3))
    emplacement = db.Column(db.String(200))
    date_maj = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fournisseur = db.Column(db.String(200))

    movements = db.relationship('InventoryMovement', backref='produit', lazy=True, cascade='all, delete-orphan')


class InventoryMovement(db.Model):
    __tablename__ = 'inventory_movements'
    id = db.Column(db.Integer, primary_key=True)
    produit_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    type_mouvement = db.Column(db.String(20))
    quantite = db.Column(db.Float, nullable=False)
    date_mouvement = db.Column(db.DateTime, default=datetime.utcnow)
    raison = db.Column(db.String(200))
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    poste = db.Column(db.String(100))
    salaire_tnd = db.Column(db.Numeric(10, 2))
    date_embauche = db.Column(db.Date)
    date_naissance = db.Column(db.Date)
    adresse = db.Column(db.Text)
    cin = db.Column(db.String(20))
    statut = db.Column(db.String(50), default='actif')
    notes = db.Column(db.Text)

    attendances = db.relationship('Attendance', backref='employe', lazy=True, cascade='all, delete-orphan')


class Attendance(db.Model):
    __tablename__ = 'attendances'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    heure_arrivee = db.Column(db.Time)
    heure_depart = db.Column(db.Time)
    heures_travaillees = db.Column(db.Float)
    statut = db.Column(db.String(50), default='present')
    notes = db.Column(db.Text)


class Harvest(db.Model):
    __tablename__ = 'harvests'
    id = db.Column(db.Integer, primary_key=True)
    culture_id = db.Column(db.Integer, db.ForeignKey('crops.id'), nullable=False)
    date_recolte = db.Column(db.Date, nullable=False)
    quantite_recoltee = db.Column(db.Float, nullable=False)
    unite = db.Column(db.String(20), default='kg')
    qualite = db.Column(db.String(50))
    pertes = db.Column(db.Float, default=0)
    main_doeuvre = db.Column(db.Integer)
    notes = db.Column(db.Text)


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))
    est_lu = db.Column(db.Boolean, default=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    lien = db.Column(db.String(500))


class AnimalType(db.Model):
    __tablename__ = 'animal_types'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    categorie = db.Column(db.String(50))
    description = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    animals = db.relationship('Animal', backref='type_animal', lazy=True)


class Animal(db.Model):
    __tablename__ = 'animals'
    id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('animal_types.id'), nullable=False)
    numero_identification = db.Column(db.String(50), unique=True)
    nom = db.Column(db.String(100))
    sexe = db.Column(db.String(10))
    date_naissance = db.Column(db.Date)
    race = db.Column(db.String(100))
    couleur = db.Column(db.String(50))
    poids_naissance = db.Column(db.Float)
    poids_actuel = db.Column(db.Float)
    statut = db.Column(db.String(50), default='actif')
    prix_achat = db.Column(db.Numeric(10, 2))
    date_achat = db.Column(db.Date)
    provenance = db.Column(db.String(200))
    parcelle_id = db.Column(db.Integer, db.ForeignKey('plots.id'))
    notes = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    soins = db.relationship('AnimalSoin', backref='animal', lazy=True, cascade='all, delete-orphan')
    productions = db.relationship('AnimalProduction', backref='animal', lazy=True, cascade='all, delete-orphan')
    alimentations = db.relationship('Alimentation', backref='animal', lazy=True, cascade='all, delete-orphan')


class AnimalSoin(db.Model):
    __tablename__ = 'animal_soins'
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animals.id'), nullable=False)
    date_soin = db.Column(db.Date, nullable=False)
    type_soin = db.Column(db.String(100))
    description = db.Column(db.Text)
    veterinaire = db.Column(db.String(200))
    cout_tnd = db.Column(db.Numeric(10, 2))
    produits_utilises = db.Column(db.Text)
    prochain_rappel = db.Column(db.Date)
    notes = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)


class AnimalProduction(db.Model):
    __tablename__ = 'animal_productions'
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animals.id'), nullable=False)
    date_production = db.Column(db.Date, nullable=False)
    type_produit = db.Column(db.String(50))
    quantite = db.Column(db.Float, nullable=False)
    unite = db.Column(db.String(20), default='L')
    prix_vente_unitaire = db.Column(db.Numeric(10, 3))
    revenu_total = db.Column(db.Numeric(10, 2))
    notes = db.Column(db.Text)


class Alimentation(db.Model):
    __tablename__ = 'alimentations'
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animals.id'), nullable=False)
    date_alimentation = db.Column(db.Date, nullable=False)
    type_nourriture = db.Column(db.String(100))
    quantite = db.Column(db.Float)
    unite = db.Column(db.String(20))
    cout_tnd = db.Column(db.Numeric(10, 2))
    notes = db.Column(db.Text)

class Proprietaire(db.Model):
    __tablename__ = 'proprietaires'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    adresse = db.Column(db.Text)
    notes = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    parts = db.relationship('PartProprietaire', backref='proprietaire', lazy=True, cascade='all, delete-orphan')
    depenses_perso = db.relationship('DepenseProprietaire', backref='proprietaire', lazy=True, cascade='all, delete-orphan')


class PartProprietaire(db.Model):
    __tablename__ = 'parts_proprietaires'
    id = db.Column(db.Integer, primary_key=True)
    proprietaire_id = db.Column(db.Integer, db.ForeignKey('proprietaires.id'), nullable=False)
    type_bien = db.Column(db.String(50), nullable=False)
    bien_id = db.Column(db.Integer, nullable=False)
    part_pct = db.Column(db.Float, nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)


class DepenseProprietaire(db.Model):
    __tablename__ = 'depenses_proprietaires'
    id = db.Column(db.Integer, primary_key=True)
    proprietaire_id = db.Column(db.Integer, db.ForeignKey('proprietaires.id'), nullable=False)
    categorie = db.Column(db.String(100), nullable=False)
    montant_tnd = db.Column(db.Numeric(10, 2), nullable=False)
    date_depense = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    type_depense = db.Column(db.String(20), default='personnelle')
    bien_type = db.Column(db.String(50))
    bien_id = db.Column(db.Integer)
    facture_fichier = db.Column(db.String(255))
    notes = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
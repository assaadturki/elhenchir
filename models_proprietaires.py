# ========== AJOUTER À LA FIN DE models/__init__.py ==========

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

    # Relations
    parts = db.relationship('PartProprietaire', backref='proprietaire', lazy=True, cascade='all, delete-orphan')
    depenses_perso = db.relationship('DepenseProprietaire', backref='proprietaire', lazy=True, cascade='all, delete-orphan')


class PartProprietaire(db.Model):
    """Part d'un propriétaire dans un bien (parcelle, animal, olivier, matériel)"""
    __tablename__ = 'parts_proprietaires'
    id = db.Column(db.Integer, primary_key=True)
    proprietaire_id = db.Column(db.Integer, db.ForeignKey('proprietaires.id'), nullable=False)
    type_bien = db.Column(db.String(50), nullable=False)  # parcelle | animal | olivier | materiel
    bien_id = db.Column(db.Integer, nullable=False)       # ID du bien concerné
    part_pct = db.Column(db.Float, nullable=False)        # Part en % (ex: 50.0)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)


class DepenseProprietaire(db.Model):
    """Dépense personnelle d'un propriétaire (hors budget commun)"""
    __tablename__ = 'depenses_proprietaires'
    id = db.Column(db.Integer, primary_key=True)
    proprietaire_id = db.Column(db.Integer, db.ForeignKey('proprietaires.id'), nullable=False)
    categorie = db.Column(db.String(100), nullable=False)
    montant_tnd = db.Column(db.Numeric(10, 2), nullable=False)
    date_depense = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    type_depense = db.Column(db.String(20), default='personnelle')  # personnelle | part_commune
    bien_type = db.Column(db.String(50))   # parcelle | animal | olivier | materiel | general
    bien_id = db.Column(db.Integer)        # ID du bien concerné (optionnel)
    facture_fichier = db.Column(db.String(255))
    notes = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

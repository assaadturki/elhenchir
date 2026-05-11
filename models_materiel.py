# ========== AJOUTER À LA FIN DE models/__init__.py ==========

class Materiel(db.Model):
    __tablename__ = 'materiels'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    type_materiel = db.Column(db.String(100))        # Tracteur, Charrue, Pompe...
    marque = db.Column(db.String(100))
    modele = db.Column(db.String(100))
    numero_serie = db.Column(db.String(100), unique=True)
    annee_achat = db.Column(db.Integer)
    prix_achat = db.Column(db.Numeric(10, 2))
    etat = db.Column(db.String(50), default='bon')   # bon | moyen | mauvais | hors_service
    parcelle_id = db.Column(db.Integer, db.ForeignKey('plots.id'))
    localisation = db.Column(db.String(200))
    notes = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    entretiens = db.relationship('EntretienMateriel', backref='materiel', lazy=True, cascade='all, delete-orphan')
    pannes = db.relationship('PanneMateriel', backref='materiel', lazy=True, cascade='all, delete-orphan')
    couts = db.relationship('CoutMateriel', backref='materiel', lazy=True, cascade='all, delete-orphan')


class EntretienMateriel(db.Model):
    __tablename__ = 'entretiens_materiel'
    id = db.Column(db.Integer, primary_key=True)
    materiel_id = db.Column(db.Integer, db.ForeignKey('materiels.id'), nullable=False)
    type_entretien = db.Column(db.String(100))       # Vidange, Revision, Graissage...
    date_entretien = db.Column(db.Date, nullable=False)
    date_prochain = db.Column(db.Date)
    description = db.Column(db.Text)
    technicien = db.Column(db.String(200))
    cout_tnd = db.Column(db.Numeric(10, 2))
    pieces_changees = db.Column(db.Text)
    notes = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)


class PanneMateriel(db.Model):
    __tablename__ = 'pannes_materiel'
    id = db.Column(db.Integer, primary_key=True)
    materiel_id = db.Column(db.Integer, db.ForeignKey('materiels.id'), nullable=False)
    date_panne = db.Column(db.Date, nullable=False)
    date_reparation = db.Column(db.Date)
    description = db.Column(db.Text, nullable=False)
    cause = db.Column(db.String(200))
    technicien = db.Column(db.String(200))
    cout_reparation = db.Column(db.Numeric(10, 2))
    statut = db.Column(db.String(50), default='en_cours')  # en_cours | repare | irrecuperable
    notes = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)


class CoutMateriel(db.Model):
    __tablename__ = 'couts_materiel'
    id = db.Column(db.Integer, primary_key=True)
    materiel_id = db.Column(db.Integer, db.ForeignKey('materiels.id'), nullable=False)
    type_cout = db.Column(db.String(50))   # carburant | reparation | piece | assurance | autre
    montant_tnd = db.Column(db.Numeric(10, 2), nullable=False)
    date_cout = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(200))
    notes = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

# ========== INSTRUCTIONS D'INTEGRATION ==========

# ---- 1. models/__init__.py ----
# Dans la classe Expense, ajouter la colonne facture_fichier :
#
#   facture_fichier = db.Column(db.String(255))  # <-- ajouter cette ligne
#
# Exemple (après la colonne 'reference') :
#
#   reference = db.Column(db.String(100))
#   fournisseur = db.Column(db.String(200))
#   facture_fichier = db.Column(db.String(255))   # <-- ICI
#   date_creation = db.Column(db.DateTime, default=datetime.utcnow)


# ---- 2. models/__init__.py ----
# Ajouter à la FIN du fichier le contenu de models_materiel.py
# (les 4 classes : Materiel, EntretienMateriel, PanneMateriel, CoutMateriel)


# ---- 3. app.py ----
# a) Dans les imports en haut, ajouter :
#    from werkzeug.utils import secure_filename
#    import uuid
#
# b) Dans les imports des modèles, ajouter :
#    from models import ... Materiel, EntretienMateriel, PanneMateriel, CoutMateriel
#
# c) Remplacer la route /expenses/create existante par celle dans routes_materiel.py
#
# d) Ajouter toutes les nouvelles routes de routes_materiel.py avant "if __name__ == '__main__':"


# ---- 4. templates/ ----
# - Copier templates/materiel/ (tous les fichiers)
# - Remplacer templates/expenses/create.html  par expenses_create.html
# - Remplacer templates/expenses/index.html   par expenses_index.html


# ---- 5. base.html ----
# Ajouter dans la sidebar, après Elevage :
#
#   <li class="nav-item">
#     <a class="nav-link" href="{{ url_for('materiel') }}">
#       <i class="fas fa-tools"></i> Matériel
#     </a>
#   </li>


# ---- 6. Migration DB ----
# Les nouvelles tables sont créées automatiquement par db.create_all()
# La colonne facture_fichier sur Expense nécessite une migration sur Render :
#
# Option A (plus simple) : Flask-Migrate
#   flask db migrate -m "ajout materiel et factures"
#   flask db upgrade
#
# Option B (sur Render, sans migration) :
#   Ajouter nullable=True sur la colonne (déjà fait), Render recréera les tables manquantes.
#   La colonne facture_fichier sera ajoutée via :
#   ALTER TABLE expenses ADD COLUMN facture_fichier VARCHAR(255);
#   (à exécuter dans la console SQL de Render ou Supabase)

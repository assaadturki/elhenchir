from app import app, db
from models import AnimalType, Animal

with app.app_context():
    # Créer le type "Autre" s'il n'existe pas
    autre_type = AnimalType.query.filter_by(nom='Autre').first()
    if not autre_type:
        autre_type = AnimalType(nom='Autre', categorie='Autre', description='Type par défaut')
        db.session.add(autre_type)
        db.session.commit()
        print("✅ Type 'Autre' créé")
    
    # Assigner le type aux animaux sans type
    animaux_sans_type = Animal.query.filter_by(type_id=None).all()
    if animaux_sans_type:
        for animal in animaux_sans_type:
            animal.type_id = autre_type.id
        db.session.commit()
        print(f"✅ {len(animaux_sans_type)} animaux mis à jour")
    
    # Vérifier qu'il n'y a plus d'animaux sans type
    restants = Animal.query.filter_by(type_id=None).count()
    if restants == 0:
        print("✅ Tous les animaux ont un type!")
    else:
        print(f"⚠️ Il reste {restants} animaux sans type")

print("🎉 Correction terminée!")
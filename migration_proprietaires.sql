-- ========== À exécuter dans pgAdmin (Render PostgreSQL) ==========

CREATE TABLE IF NOT EXISTS proprietaires (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100),
    telephone VARCHAR(20),
    email VARCHAR(100),
    adresse TEXT,
    notes TEXT,
    date_creation TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS parts_proprietaires (
    id SERIAL PRIMARY KEY,
    proprietaire_id INTEGER NOT NULL REFERENCES proprietaires(id) ON DELETE CASCADE,
    type_bien VARCHAR(50) NOT NULL,
    bien_id INTEGER NOT NULL,
    part_pct FLOAT NOT NULL,
    date_creation TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS depenses_proprietaires (
    id SERIAL PRIMARY KEY,
    proprietaire_id INTEGER NOT NULL REFERENCES proprietaires(id) ON DELETE CASCADE,
    categorie VARCHAR(100) NOT NULL,
    montant_tnd NUMERIC(10,2) NOT NULL,
    date_depense DATE NOT NULL,
    description TEXT,
    type_depense VARCHAR(20) DEFAULT 'personnelle',
    bien_type VARCHAR(50),
    bien_id INTEGER,
    facture_fichier VARCHAR(255),
    notes TEXT,
    date_creation TIMESTAMP DEFAULT NOW()
);

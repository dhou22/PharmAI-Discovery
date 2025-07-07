-- Remove the CREATE DATABASE and \c commands since the database is already created
-- The container automatically connects to the mediagent database

-- Compounds table
CREATE TABLE compounds (
    id SERIAL PRIMARY KEY,
    chembl_id VARCHAR(20) UNIQUE,
    pubchem_cid INTEGER,
    smiles TEXT NOT NULL,
    molecular_formula VARCHAR(100),
    molecular_weight DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bioactivities table
CREATE TABLE bioactivities (
    id SERIAL PRIMARY KEY,
    compound_id INTEGER REFERENCES compounds(id),
    target_chembl_id VARCHAR(20),
    standard_type VARCHAR(50),
    standard_value DECIMAL(15,6),
    standard_units VARCHAR(20),
    pchembl_value DECIMAL(4,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analysis results table
CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    compound_id INTEGER REFERENCES compounds(id),
    analysis_type VARCHAR(50),
    results JSONB,
    confidence_score DECIMAL(4,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_compounds_chembl ON compounds(chembl_id);
CREATE INDEX idx_compounds_smiles ON compounds USING hash(smiles);
CREATE INDEX idx_bioactivities_compound ON bioactivities(compound_id);
CREATE INDEX idx_analysis_compound ON analysis_results(compound_id);
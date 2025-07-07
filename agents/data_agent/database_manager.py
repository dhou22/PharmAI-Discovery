# Fixed DatabaseManager with better error handling and ALL required methods

import psycopg2
import psycopg2.extras
import json
import os
from typing import Dict, List, Optional
import logging

class DatabaseManager:
    """Database operations for MediAgent with improved error handling"""
    
    def __init__(self, host=None, port=None, database=None, user=None, password=None):
        # Use environment variables or defaults
        # Handle both Docker and local development
        default_host = os.getenv('DB_HOST', 'postgres')
        
        # If running locally (not in Docker), use localhost
        if default_host == 'postgres':
            try:
                import socket
                socket.gethostbyname('postgres')
            except socket.gaierror:
                default_host = 'localhost'
        
        self.connection_params = {
            'host': host or default_host,
            'port': port or int(os.getenv('DB_PORT', '5432')),
            'database': database or os.getenv('DB_NAME', 'mediagent'),
            'user': user or os.getenv('DB_USER', 'admin'),
            'password': password or os.getenv('DB_PASSWORD', 'mediagent2025')
        }
        
        # Log connection attempt (without password)
        safe_params = {k: v for k, v in self.connection_params.items() if k != 'password'}
        logging.info(f"Database connection params: {safe_params}")
        
    def get_connection(self):
        """Get database connection with better error handling"""
        try:
            conn = psycopg2.connect(**self.connection_params)
            return conn
        except psycopg2.OperationalError as e:
            logging.error(f"Database connection failed: {e}")
            
            # Try localhost if postgres hostname failed
            if self.connection_params['host'] == 'postgres':
                alt_params = self.connection_params.copy()
                alt_params['host'] = 'localhost'
                
                try:
                    logging.info("Trying localhost instead of postgres hostname...")
                    conn = psycopg2.connect(**alt_params)
                    self.connection_params = alt_params  # Update if successful
                    return conn
                except psycopg2.OperationalError as e2:
                    logging.error(f"Localhost connection also failed: {e2}")
            
            # Try alternative credentials
            alt_params = self.connection_params.copy()
            alt_params['user'] = 'admin'
            alt_params['password'] = 'mediagent'
            
            try:
                logging.info("Trying alternative credentials...")
                conn = psycopg2.connect(**alt_params)
                self.connection_params = alt_params  # Update if successful
                return conn
            except psycopg2.OperationalError as e2:
                logging.error(f"Alternative credentials also failed: {e2}")
                raise e
    
    def test_connection(self):
        """Test database connection and return status"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version()")
                    version = cur.fetchone()[0]
                    logging.info(f"Database connection successful. Version: {version}")
                    return True, version
        except Exception as e:
            logging.error(f"Database connection test failed: {e}")
            return False, str(e)
    
    def insert_compound(self, compound_data: Dict) -> Optional[int]:
        """Insert compound into database with better error handling"""
        query = """
        INSERT INTO compounds (chembl_id, pubchem_cid, smiles, molecular_formula, 
                             molecular_weight, pref_name, bioactivities_count)
        VALUES (%(chembl_id)s, %(pubchem_cid)s, %(smiles)s, %(molecular_formula)s, 
                %(molecular_weight)s, %(pref_name)s, %(bioactivities_count)s)
        ON CONFLICT (chembl_id) DO UPDATE SET
            pubchem_cid = EXCLUDED.pubchem_cid,
            smiles = EXCLUDED.smiles,
            molecular_formula = EXCLUDED.molecular_formula,
            molecular_weight = EXCLUDED.molecular_weight,
            pref_name = EXCLUDED.pref_name,
            bioactivities_count = EXCLUDED.bioactivities_count,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id;
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Prepare data with defaults for missing fields
                    data = {
                        'chembl_id': compound_data.get('chembl_id'),
                        'pubchem_cid': compound_data.get('pubchem_cid'),
                        'smiles': compound_data.get('smiles'),
                        'molecular_formula': compound_data.get('molecular_formula'),
                        'molecular_weight': compound_data.get('molecular_weight'),
                        'pref_name': compound_data.get('pref_name'),
                        'bioactivities_count': compound_data.get('bioactivities_count', 0)
                    }
                    
                    logging.info(f"Inserting compound: {data['chembl_id']}")
                    cur.execute(query, data)
                    result = cur.fetchone()
                    compound_id = result[0] if result else None
                    
                    if compound_id:
                        logging.info(f"Successfully inserted/updated compound {data['chembl_id']} with ID {compound_id}")
                    
                    return compound_id
                    
        except Exception as e:
            logging.error(f"Database insert error for {compound_data.get('chembl_id')}: {e}")
            return None
    
    def update_compound(self, chembl_id: str, compound_data: Dict) -> bool:
        """Update compound in database - MISSING METHOD ADDED"""
        query = """
        UPDATE compounds SET 
            pubchem_cid = %(pubchem_cid)s,
            smiles = %(smiles)s,
            molecular_formula = %(molecular_formula)s,
            molecular_weight = %(molecular_weight)s,
            pref_name = %(pref_name)s,
            bioactivities_count = %(bioactivities_count)s,
            updated_at = CURRENT_TIMESTAMP
        WHERE chembl_id = %(chembl_id)s
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Prepare data with the chembl_id
                    data = compound_data.copy()
                    data['chembl_id'] = chembl_id
                    
                    # Set defaults for missing fields
                    data.setdefault('pubchem_cid', None)
                    data.setdefault('smiles', None)
                    data.setdefault('molecular_formula', None)
                    data.setdefault('molecular_weight', None)
                    data.setdefault('pref_name', None)
                    data.setdefault('bioactivities_count', 0)
                    
                    logging.info(f"Updating compound: {chembl_id}")
                    cur.execute(query, data)
                    rows_affected = cur.rowcount
                    
                    if rows_affected > 0:
                        logging.info(f"Successfully updated compound {chembl_id}")
                        return True
                    else:
                        logging.warning(f"No rows updated for compound {chembl_id}")
                        return False
                        
        except Exception as e:
            logging.error(f"Database update error for {chembl_id}: {e}")
            return False
    
    def get_compound_cross_references(self, chembl_id: str) -> List[Dict]:
        """Get compound cross-references - MISSING METHOD ADDED"""
        # This would typically be a separate table, but for now we'll return empty
        # You might need to implement this based on your database schema
        logging.info(f"Getting cross-references for {chembl_id} - not implemented yet")
        return []
    
    def sync(self):
        """Sync/commit database changes - MISSING METHOD ADDED"""
        try:
            # For psycopg2, we use context managers which auto-commit
            # This method is here for compatibility
            logging.info("Database sync called - using auto-commit via context managers")
            return True
        except Exception as e:
            logging.error(f"Database sync error: {e}")
            return False
    
    def insert_bioactivities(self, compound_id: int, bioactivities: List[Dict]) -> bool:
        """Insert bioactivity data"""
        if not bioactivities:
            return True
            
        query = """
        INSERT INTO bioactivities (compound_id, target_chembl_id, standard_type, 
                                 standard_value, standard_units, pchembl_value)
        VALUES (%(compound_id)s, %(target_chembl_id)s, %(standard_type)s,
                %(standard_value)s, %(standard_units)s, %(pchembl_value)s)
        ON CONFLICT (compound_id, target_chembl_id, standard_type) DO UPDATE SET
            standard_value = EXCLUDED.standard_value,
            standard_units = EXCLUDED.standard_units,
            pchembl_value = EXCLUDED.pchembl_value,
            updated_at = CURRENT_TIMESTAMP
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    for activity in bioactivities:
                        activity['compound_id'] = compound_id
                        cur.execute(query, activity)
                    logging.info(f"Inserted {len(bioactivities)} bioactivities for compound {compound_id}")
            return True
        except Exception as e:
            logging.error(f"Bioactivity insert error: {e}")
            return False
    
    def get_compound_by_chembl_id(self, chembl_id: str) -> Optional[Dict]:
        """Get compound by ChEMBL ID"""
        query = "SELECT * FROM compounds WHERE chembl_id = %s"
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(query, (chembl_id,))
                    result = cur.fetchone()
                    if result:
                        compound = dict(result)
                        logging.info(f"Found compound {chembl_id} in database")
                        return compound
                    else:
                        logging.info(f"Compound {chembl_id} not found in database")
                        return None
        except Exception as e:
            logging.error(f"Database query error for {chembl_id}: {e}")
            return None
    
    def search_compounds(self, query: str, limit: int = 20) -> List[Dict]:
        """Search compounds by various criteria"""
        sql = """
        SELECT * FROM compounds 
        WHERE chembl_id ILIKE %s 
           OR molecular_formula ILIKE %s
           OR smiles ILIKE %s
           OR pref_name ILIKE %s
        ORDER BY chembl_id
        LIMIT %s
        """
        
        search_term = f"%{query}%"
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(sql, (search_term, search_term, search_term, search_term, limit))
                    results = cur.fetchall()
                    compounds = [dict(row) for row in results]
                    logging.info(f"Found {len(compounds)} compounds matching query: {query}")
                    return compounds
        except Exception as e:
            logging.error(f"Database search error: {e}")
            return []
    
    def get_compound_count(self) -> int:
        """Get total number of compounds in database"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM compounds")
                    count = cur.fetchone()[0]
                    logging.info(f"Total compounds in database: {count}")
                    return count
        except Exception as e:
            logging.error(f"Error getting compound count: {e}")
            return 0
    
    def create_tables_if_not_exist(self):
        """Create tables if they don't exist"""
        compounds_table = """
        CREATE TABLE IF NOT EXISTS compounds (
            id SERIAL PRIMARY KEY,
            chembl_id VARCHAR(20) UNIQUE NOT NULL,
            pubchem_cid VARCHAR(20),
            smiles TEXT,
            molecular_formula VARCHAR(100),
            molecular_weight FLOAT,
            pref_name TEXT,
            bioactivities_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        bioactivities_table = """
        CREATE TABLE IF NOT EXISTS bioactivities (
            id SERIAL PRIMARY KEY,
            compound_id INTEGER REFERENCES compounds(id),
            target_chembl_id VARCHAR(20),
            standard_type VARCHAR(50),
            standard_value FLOAT,
            standard_units VARCHAR(20),
            pchembl_value FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(compound_id, target_chembl_id, standard_type)
        );
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(compounds_table)
                    cur.execute(bioactivities_table)
                    logging.info("Tables created/verified successfully")
                    return True
        except Exception as e:
            logging.error(f"Error creating tables: {e}")
            return False

# Test database connection with multiple credential attempts
if __name__ == "__main__":
    # Test with automatic host detection
    db = DatabaseManager()
    
    # Test connection
    success, message = db.test_connection()
    if success:
        print(f"✅ Database connection successful! {message}")
        
        # Create tables if needed
        if db.create_tables_if_not_exist():
            print("✅ Tables created/verified successfully")
        
        # Test compound count
        count = db.get_compound_count()
        print(f"Current compounds in database: {count}")
        
        # Test compound operations
        test_compound = {
            'chembl_id': 'CHEMBL_TEST_001',
            'pref_name': 'Test Compound',
            'molecular_formula': 'C8H9NO2',
            'molecular_weight': 151.16,
            'smiles': 'CC(=O)Nc1ccc(O)cc1',
            'pubchem_cid': '1983',
            'bioactivities_count': 5
        }
        
        print("\n🧪 Testing compound operations...")
        
        # Test insert
        compound_id = db.insert_compound(test_compound)
        if compound_id:
            print(f"✅ Test compound inserted with ID: {compound_id}")
        
        # Test get
        retrieved = db.get_compound_by_chembl_id('CHEMBL_TEST_001')
        if retrieved:
            print(f"✅ Test compound retrieved: {retrieved['pref_name']}")
        
        # Test update
        updated_data = {'pref_name': 'Updated Test Compound', 'bioactivities_count': 10}
        if db.update_compound('CHEMBL_TEST_001', updated_data):
            print("✅ Test compound updated successfully")
        
        # Test search
        results = db.search_compounds('test', limit=5)
        print(f"✅ Search found {len(results)} compounds")
        
    else:
        print(f"❌ Database connection failed: {message}")
        
        # Suggest fixes
        print("\n🔧 Suggested fixes:")
        print("1. Check if PostgreSQL container is running: docker ps | grep postgres")
        print("2. Check PostgreSQL logs: docker logs mediagent-postgres")
        print("3. Verify credentials in docker-compose.yml")
        print("4. Run the script inside Docker: docker-compose exec data-agent python database_manager.py")
        print("5. Or use localhost if running locally: DB_HOST=localhost python database_manager.py")
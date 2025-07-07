# chembl_connector.py (COMPLETELY FIXED VERSION)
import requests
import pandas as pd
import logging
from typing import Dict, List, Optional
import time

class ChEMBLConnector:
    """
    ChEMBL API connector for molecular data extraction - COMPLETELY FIXED VERSION
    """
    
    def __init__(self, base_url: str = "https://www.ebi.ac.uk/chembl/api/data"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.delay = 0.1
        self.logger = logging.getLogger(__name__)
        
    def _safe_extract(self, data: any, default=None) -> any:
        """Safely extract value from ChEMBL response"""
        if data is None:
            return default
        if isinstance(data, list):
            return data[0] if data and data[0] is not None else default
        return data if data != "" else default
    
    def _process_compound_data(self, compound_data: Dict) -> Dict:
        """Process compound data from ChEMBL API - COMPLETELY FIXED VERSION"""
        processed = {}
        
        # Debug: Log the raw data structure
        self.logger.info(f"Processing compound data keys: {list(compound_data.keys())}")
        
        # Basic info
        processed['chembl_id'] = compound_data.get('molecule_chembl_id')
        processed['pref_name'] = compound_data.get('pref_name')
        processed['max_phase'] = compound_data.get('max_phase')
        
        # CRITICAL FIX: Multiple ways to extract molecular properties
        mol_props = None
        
        # Method 1: Direct molecule_properties access
        if 'molecule_properties' in compound_data and compound_data['molecule_properties']:
            mol_props = compound_data['molecule_properties']
            self.logger.info(f"Found molecule_properties: {mol_props}")
        
        # Method 2: Check if properties are at root level
        elif any(key in compound_data for key in ['molecular_formula', 'molecular_weight']):
            mol_props = compound_data
            self.logger.info("Found properties at root level")
        
        # Method 3: Check for nested properties structure
        elif 'properties' in compound_data:
            mol_props = compound_data['properties']
            self.logger.info("Found properties in nested structure")
        
        # Extract molecular properties with multiple fallbacks
        if mol_props:
            # Try different possible field names for molecular formula
            processed['molecular_formula'] = (
                mol_props.get('molecular_formula') or 
                mol_props.get('molformula') or 
                mol_props.get('formula')
            )
            
            # Try different possible field names for molecular weight
            processed['molecular_weight'] = (
                mol_props.get('molecular_weight') or 
                mol_props.get('mw_monoisotopic') or 
                mol_props.get('mw_freebase') or
                mol_props.get('weight')
            )
            
            # Other properties
            processed['num_ro5_violations'] = mol_props.get('num_ro5_violations')
            processed['alogp'] = mol_props.get('alogp')
            processed['hbd'] = mol_props.get('hbd')
            processed['hba'] = mol_props.get('hba')
            processed['psa'] = mol_props.get('psa')
            processed['rtb'] = mol_props.get('rtb')
        else:
            self.logger.warning(f"No molecular properties found for {processed['chembl_id']}")
            processed['molecular_formula'] = None
            processed['molecular_weight'] = None
        
        # CRITICAL FIX: Multiple ways to extract structure info
        mol_struct = None
        
        # Method 1: Direct molecule_structures access
        if 'molecule_structures' in compound_data and compound_data['molecule_structures']:
            mol_struct = compound_data['molecule_structures']
            self.logger.info(f"Found molecule_structures: {mol_struct}")
        
        # Method 2: Check if structure data is at root level
        elif any(key in compound_data for key in ['canonical_smiles', 'smiles']):
            mol_struct = compound_data
            self.logger.info("Found structure data at root level")
        
        # Method 3: Check for nested structure
        elif 'structures' in compound_data:
            mol_struct = compound_data['structures']
            self.logger.info("Found structures in nested format")
        
        # Extract structure information with multiple fallbacks
        if mol_struct:
            processed['smiles'] = (
                mol_struct.get('canonical_smiles') or 
                mol_struct.get('smiles') or
                mol_struct.get('structure_smiles')
            )
            processed['inchi'] = (
                mol_struct.get('standard_inchi') or 
                mol_struct.get('inchi')
            )
            processed['inchi_key'] = (
                mol_struct.get('standard_inchi_key') or 
                mol_struct.get('inchi_key')
            )
        else:
            self.logger.warning(f"No structure data found for {processed['chembl_id']}")
            processed['smiles'] = None
            processed['inchi'] = None
            processed['inchi_key'] = None
        
        # CRITICAL FIX: Enhanced cross references extraction for PubChem
        pubchem_cid = None
        
        # Method 1: Direct cross_references access
        if 'cross_references' in compound_data and compound_data['cross_references']:
            cross_refs = compound_data['cross_references']
            self.logger.info(f"Found {len(cross_refs)} cross references")
            
            for ref in cross_refs:
                if isinstance(ref, dict):
                    xref_src = ref.get('xref_src', '').lower()
                    if 'pubchem' in xref_src:
                        pubchem_cid = ref.get('xref_id')
                        self.logger.info(f"Found PubChem CID: {pubchem_cid}")
                        break
        
        # Method 2: Check for direct pubchem_cid field
        elif 'pubchem_cid' in compound_data:
            pubchem_cid = compound_data['pubchem_cid']
            self.logger.info(f"Found direct PubChem CID: {pubchem_cid}")
        
        # Method 3: Check for alternative field names
        elif 'cid' in compound_data:
            pubchem_cid = compound_data['cid']
            self.logger.info(f"Found CID field: {pubchem_cid}")
        
        processed['pubchem_cid'] = pubchem_cid
        
        # Log extraction results
        self.logger.info(f"Final extraction for {processed['chembl_id']}:")
        self.logger.info(f"  - Formula: {processed.get('molecular_formula')}")
        self.logger.info(f"  - Weight: {processed.get('molecular_weight')}")
        self.logger.info(f"  - SMILES: {processed.get('smiles')}")
        self.logger.info(f"  - PubChem CID: {processed.get('pubchem_cid')}")
        
        return processed
    
    def search_compounds(self, query: str, limit: int = 20) -> List[Dict]:
        """Search compounds by query - ENHANCED VERSION"""
        endpoint = f"{self.base_url}/molecule/search"
        params = {
            'q': query,
            'limit': limit,
            'format': 'json'
        }
        
        try:
            time.sleep(self.delay)
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            molecules = data.get('molecules', [])
            self.logger.info(f"ChEMBL search returned {len(molecules)} compounds")
            
            compounds = []
            for i, compound in enumerate(molecules):
                self.logger.info(f"Processing search result {i+1}/{len(molecules)}")
                
                # Get ChEMBL ID
                chembl_id = compound.get('molecule_chembl_id')
                if not chembl_id:
                    self.logger.warning(f"No ChEMBL ID in search result {i+1}")
                    continue
                
                # For search results, we need to get detailed info
                # because search results often don't include all properties
                detailed_compound = self.get_compound_with_enriched_data(chembl_id)
                
                if detailed_compound:
                    compounds.append(detailed_compound)
                    self.logger.info(f"Successfully processed {chembl_id}")
                else:
                    # Fallback to basic processing
                    self.logger.warning(f"Could not get detailed info for {chembl_id}, using basic data")
                    processed = self._process_compound_data(compound)
                    compounds.append(processed)
                
            return compounds
            
        except Exception as e:
            self.logger.error(f"ChEMBL search error: {e}")
            return []
    
    def get_compound_with_enriched_data(self, chembl_id: str) -> Optional[Dict]:
        """Get compound with enriched data - ENHANCED VERSION"""
        endpoint = f"{self.base_url}/molecule/{chembl_id}"
        params = {
            'format': 'json'
        }
        
        try:
            time.sleep(self.delay)
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            compound_data = response.json()
            
            self.logger.info(f"Retrieved detailed data for {chembl_id}")
            self.logger.debug(f"Raw compound data keys: {list(compound_data.keys())}")
            
            # Process the compound data
            processed = self._process_compound_data(compound_data)
            
            # If we're still missing critical data, try alternative endpoints
            if not processed.get('molecular_formula') or not processed.get('molecular_weight'):
                self.logger.info(f"Missing molecular data for {chembl_id}, trying alternative endpoints...")
                
                # Try molecule properties endpoint
                props_data = self._get_molecule_properties(chembl_id)
                if props_data:
                    # Merge properties data
                    for key, value in props_data.items():
                        if value is not None and not processed.get(key):
                            processed[key] = value
                
                # Try molecule structures endpoint
                struct_data = self._get_molecule_structures(chembl_id)
                if struct_data:
                    # Merge structure data
                    for key, value in struct_data.items():
                        if value is not None and not processed.get(key):
                            processed[key] = value
            
            return processed
            
        except Exception as e:
            self.logger.error(f"ChEMBL compound details error for {chembl_id}: {e}")
            return None
    
    def _get_molecule_properties(self, chembl_id: str) -> Optional[Dict]:
        """Get molecule properties from dedicated endpoint"""
        endpoint = f"{self.base_url}/molecule/{chembl_id}/properties"
        
        try:
            time.sleep(self.delay)
            response = self.session.get(endpoint)
            response.raise_for_status()
            data = response.json()
            
            properties = data.get('properties', [])
            if properties:
                props = properties[0]  # Take first property set
                return {
                    'molecular_formula': props.get('molecular_formula'),
                    'molecular_weight': props.get('molecular_weight'),
                    'alogp': props.get('alogp'),
                    'hbd': props.get('hbd'),
                    'hba': props.get('hba'),
                    'psa': props.get('psa'),
                    'rtb': props.get('rtb'),
                    'num_ro5_violations': props.get('num_ro5_violations')
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting molecule properties for {chembl_id}: {e}")
            return None
    
    def _get_molecule_structures(self, chembl_id: str) -> Optional[Dict]:
        """Get molecule structures from dedicated endpoint"""
        endpoint = f"{self.base_url}/molecule/{chembl_id}/structures"
        
        try:
            time.sleep(self.delay)
            response = self.session.get(endpoint)
            response.raise_for_status()
            data = response.json()
            
            structures = data.get('structures', [])
            if structures:
                struct = structures[0]  # Take first structure
                return {
                    'smiles': struct.get('canonical_smiles'),
                    'inchi': struct.get('standard_inchi'),
                    'inchi_key': struct.get('standard_inchi_key')
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting molecule structures for {chembl_id}: {e}")
            return None
    
    def get_bioactivities(self, chembl_id: str, limit: int = 100) -> List[Dict]:
        """Get bioactivity data for compound"""
        endpoint = f"{self.base_url}/activity"
        params = {
            'molecule_chembl_id': chembl_id,
            'limit': limit,
            'format': 'json'
        }
        
        try:
            time.sleep(self.delay)
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            activities = data.get('activities', [])
            self.logger.info(f"Retrieved {len(activities)} bioactivities for {chembl_id}")
            return activities
        except Exception as e:
            self.logger.error(f"Bioactivity error for {chembl_id}: {e}")
            return []

# Test the connector directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    connector = ChEMBLConnector()
    
    # Test search
    print("Testing ChEMBL search...")
    compounds = connector.search_compounds("aspirin", limit=2)
    
    for compound in compounds:
        print(f"\nCompound: {compound.get('chembl_id')}")
        print(f"Name: {compound.get('pref_name')}")
        print(f"Formula: {compound.get('molecular_formula')}")
        print(f"Weight: {compound.get('molecular_weight')}")
        print(f"PubChem CID: {compound.get('pubchem_cid')}")
        print(f"SMILES: {compound.get('smiles')}")
        
        # Test if we have the essential data
        if compound.get('molecular_formula') and compound.get('molecular_weight'):
            print("✅ Essential molecular data found!")
        else:
            print("❌ Missing essential molecular data!")
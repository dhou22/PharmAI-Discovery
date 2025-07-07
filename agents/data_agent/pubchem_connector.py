# pubchem_connector.py (ENHANCED VERSION)
import requests
import time
import logging
from typing import Dict, List, Optional

class PubChemConnector:
    """
    PubChem API connector for molecular data enrichment - ENHANCED VERSION
    """
    
    def __init__(self, base_url: str = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.delay = 0.2  # PubChem has rate limits
        self.logger = logging.getLogger(__name__)
        
    def search_by_name(self, compound_name: str) -> Optional[Dict]:
        """Search compound by name and return properties"""
        try:
            # First, get CID from name
            cid = self._get_cid_from_name(compound_name)
            if not cid:
                self.logger.warning(f"Could not find CID for compound: {compound_name}")
                return None
            
            # Then get properties using CID
            return self._get_compound_properties(cid)
            
        except Exception as e:
            self.logger.error(f"PubChem search error for {compound_name}: {e}")
            return None
    
    def search_by_smiles(self, smiles: str) -> Optional[Dict]:
        """Search compound by SMILES and return properties"""
        try:
            # Get CID from SMILES
            cid = self._get_cid_from_smiles(smiles)
            if not cid:
                self.logger.warning(f"Could not find CID for SMILES: {smiles}")
                return None
            
            # Then get properties using CID
            return self._get_compound_properties(cid)
            
        except Exception as e:
            self.logger.error(f"PubChem SMILES search error: {e}")
            return None
    
    def _get_cid_from_name(self, compound_name: str) -> Optional[str]:
        """Get CID from compound name"""
        url = f"{self.base_url}/compound/name/{compound_name}/cids/JSON"
        
        try:
            time.sleep(self.delay)
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            cids = data.get('IdentifierList', {}).get('CID', [])
            if cids:
                return str(cids[0])  # Return first CID
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting CID from name {compound_name}: {e}")
            return None
    
    def _get_cid_from_smiles(self, smiles: str) -> Optional[str]:
        """Get CID from SMILES"""
        url = f"{self.base_url}/compound/smiles/{smiles}/cids/JSON"
        
        try:
            time.sleep(self.delay)
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            cids = data.get('IdentifierList', {}).get('CID', [])
            if cids:
                return str(cids[0])  # Return first CID
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting CID from SMILES: {e}")
            return None
    
    def _get_compound_properties(self, cid: str) -> Optional[Dict]:
        """Get compound properties by CID"""
        properties = [
            'MolecularFormula',
            'MolecularWeight',
            'CanonicalSMILES',
            'IUPACName',
            'InChI',
            'InChIKey'
        ]
        
        properties_str = ','.join(properties)
        url = f"{self.base_url}/compound/cid/{cid}/property/{properties_str}/JSON"
        
        try:
            time.sleep(self.delay)
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            properties_data = data.get('PropertyTable', {}).get('Properties', [])
            if properties_data:
                compound_data = properties_data[0]
                compound_data['CID'] = cid
                self.logger.info(f"Retrieved PubChem data for CID {cid}: {compound_data}")
                return compound_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting properties for CID {cid}: {e}")
            return None

# Test the connector directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    connector = PubChemConnector()
    
    # Test search by name
    print("Testing PubChem search by name...")
    result = connector.search_by_name("aspirin")
    if result:
        print(f"Formula: {result.get('MolecularFormula')}")
        print(f"Weight: {result.get('MolecularWeight')}")
        print(f"CID: {result.get('CID')}")
        print(f"SMILES: {result.get('CanonicalSMILES')}")
    else:
        print("No results found")
    
    # Test search by SMILES
    print("\nTesting PubChem search by SMILES...")
    result = connector.search_by_smiles("CC(=O)Oc1ccccc1C(=O)O")
    if result:
        print(f"Formula: {result.get('MolecularFormula')}")
        print(f"Weight: {result.get('MolecularWeight')}")
        print(f"CID: {result.get('CID')}")
    else:
        print("No results found")
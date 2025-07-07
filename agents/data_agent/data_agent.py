# data_agent.py (COMPLETE FIXED VERSION)
from typing import Dict, List, Optional
import logging
from chembl_connector import ChEMBLConnector
from pubchem_connector import PubChemConnector
from database_manager import DatabaseManager
import os
import requests

class DataAgent:
    """
    Enhanced Data Agent with Ollama integration for AI-powered analysis
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection or DatabaseManager()
        self.chembl_connector = ChEMBLConnector()
        self.pubchem_connector = PubChemConnector()
        self.logger = logging.getLogger(__name__)
        
        # Ollama configuration
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://mediagent-ollama:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.2:latest')  # Default model
        self.current_model = None  # Track the actual model being used
        
        # Set up logging
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO)
            
        # Initialize Ollama connection and detect model
        self._initialize_ollama()
    
    def _initialize_ollama(self):
        """Initialize Ollama connection and detect available models"""
        try:
            self.logger.info("Initializing Ollama connection...")
            
            # Check if Ollama is available
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model['name'] for model in models_data.get('models', [])]
                
                self.logger.info(f"✅ Ollama connected. Available models: {available_models}")
                
                # Set the current model
                if available_models:
                    # Use the specified model if available, otherwise use the first available
                    if self.ollama_model in available_models:
                        self.current_model = self.ollama_model
                    else:
                        self.current_model = available_models[0]
                        self.logger.warning(f"Model {self.ollama_model} not available, using {self.current_model}")
                    
                    self.logger.info(f"🤖 Using Ollama model: {self.current_model}")
                else:
                    self.logger.warning("🤖 No models available in Ollama")
                    self.current_model = None
            else:
                self.logger.warning(f"🤖 Could not connect to Ollama at {self.ollama_host}")
                self.current_model = None
                
        except Exception as e:
            self.logger.error(f"Error initializing Ollama: {e}")
            self.current_model = None
    
    def get_ollama_model_info(self) -> Dict:
        """Get information about the current Ollama model"""
        try:
            if not self.current_model:
                return {
                    'model': None,
                    'status': 'unavailable',
                    'message': 'Ollama not initialized or no models available'
                }
            
            # Get detailed model information
            response = requests.post(
                f"{self.ollama_host}/api/show",
                json={"name": self.current_model},
                timeout=10
            )
            
            if response.status_code == 200:
                model_info = response.json()
                return {
                    'model': self.current_model,
                    'status': 'available',
                    'details': {
                        'name': model_info.get('details', {}).get('family', 'Unknown'),
                        'size': model_info.get('size', 'Unknown'),
                        'modified': model_info.get('modified_at', 'Unknown'),
                        'parameters': model_info.get('details', {}).get('parameter_count', 'Unknown')
                    }
                }
            else:
                return {
                    'model': self.current_model,
                    'status': 'error',
                    'message': f"Could not get model details: {response.status_code}"
                }
                
        except Exception as e:
            return {
                'model': self.current_model,
                'status': 'error',
                'message': f"Error getting model info: {e}"
            }
    
    def analyze_compound_with_ai(self, compound_data: Dict) -> Dict:
        """Analyze compound using Ollama AI model"""
        try:
            if not self.current_model:
                return {
                    'success': False,
                    'error': 'No Ollama model available',
                    'model_used': None
                }
            
            # Create a prompt for compound analysis
            prompt = f"""
            Analyze this chemical compound and provide insights:
            
            Compound: {compound_data.get('pref_name', 'Unknown')}
            ChEMBL ID: {compound_data.get('chembl_id', 'Unknown')}
            Molecular Formula: {compound_data.get('molecular_formula', 'Unknown')}
            Molecular Weight: {compound_data.get('molecular_weight', 'Unknown')}
            SMILES: {compound_data.get('smiles', 'Unknown')}
            Bioactivities Count: {compound_data.get('bioactivities_count', 0)}
            
            Please provide:
            1. Brief description of the compound
            2. Potential therapeutic uses
            3. Key chemical properties
            4. Any notable characteristics
            
            Keep the response concise and factual.
            """
            
            # Make request to Ollama
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.current_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'analysis': result.get('response', ''),
                    'model_used': self.current_model,
                    'model_info': self.get_ollama_model_info()
                }
            else:
                return {
                    'success': False,
                    'error': f"Ollama API error: {response.status_code}",
                    'model_used': self.current_model
                }
                
        except Exception as e:
            self.logger.error(f"Error analyzing compound with AI: {e}")
            return {
                'success': False,
                'error': str(e),
                'model_used': self.current_model
            }
    
    def process_compound_query(self, query: str, limit: int = 10, include_ai_analysis: bool = False) -> Dict:
        """
        Enhanced compound query processing with optional AI analysis
        """
        try:
            self.logger.info(f"Processing compound query: {query}")
            
            # Get model info for the response
            model_info = self.get_ollama_model_info()
            
            # Search ChEMBL for compounds
            compounds = self.chembl_connector.search_compounds(query, limit)
            self.logger.info(f"ChEMBL returned {len(compounds)} compounds")
            
            # Enrich each compound with additional data
            enriched_compounds = []
            for i, compound in enumerate(compounds):
                self.logger.info(f"Enriching compound {i+1}/{len(compounds)}: {compound.get('chembl_id')}")
                enriched = self._enrich_compound_data(compound)
                
                if enriched:
                    # Add AI analysis if requested
                    if include_ai_analysis and self.current_model:
                        ai_analysis = self.analyze_compound_with_ai(enriched)
                        enriched['ai_analysis'] = ai_analysis
                    
                    enriched_compounds.append(enriched)
            
            # Store in database if available
            if self.db and enriched_compounds:
                self._store_compounds(enriched_compounds)
            
            self.logger.info(f"Successfully processed {len(enriched_compounds)} compounds")
            return {
                'success': True,
                'data': {
                    'compounds': enriched_compounds,
                    'compounds_found': len(enriched_compounds),
                    'query': query,
                    'ai_analysis_included': include_ai_analysis
                },
                'model_info': model_info  # Include model info in response
            }
            
        except Exception as e:
            self.logger.error(f"Error processing compound query: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {
                    'compounds': [],
                    'compounds_found': 0,
                    'query': query
                },
                'model_info': self.get_ollama_model_info()
            }
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status including Ollama model info"""
        try:
            # Get database status
            db_status = "connected" if self.db else "not_connected"
            
            # Get Ollama status
            ollama_status = self.get_ollama_model_info()
            
            # Get connector status
            chembl_status = "available" if self.chembl_connector else "unavailable"
            pubchem_status = "available" if self.pubchem_connector else "unavailable"
            
            return {
                'database': db_status,
                'ollama': ollama_status,
                'connectors': {
                    'chembl': chembl_status,
                    'pubchem': pubchem_status
                },
                'host_info': {
                    'ollama_host': self.ollama_host,
                    'configured_model': self.ollama_model
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {
                'error': str(e),
                'ollama': self.get_ollama_model_info()
            }
    def _enrich_compound_data(self, compound: Dict) -> Optional[Dict]:
        """
        Enrich compound data with additional information from multiple sources - COMPLETE FIXED VERSION
        """
        try:
            chembl_id = compound.get('chembl_id')
            if not chembl_id:
                self.logger.warning("No ChEMBL ID found in compound data")
                return None
            
            self.logger.info(f"Enriching compound {chembl_id}")
            
            # Start with the compound data we have
            enriched_compound = compound.copy()
            
            # Log current state
            self.logger.info(f"Initial data for {chembl_id}:")
            self.logger.info(f"  - Formula: {enriched_compound.get('molecular_formula')}")
            self.logger.info(f"  - Weight: {enriched_compound.get('molecular_weight')}")
            self.logger.info(f"  - SMILES: {enriched_compound.get('smiles')}")
            self.logger.info(f"  - PubChem CID: {enriched_compound.get('pubchem_cid')}")
            
            # STEP 1: Get complete ChEMBL data with proper structure parsing
            self.logger.info("Step 1: Fetching complete ChEMBL data...")
            detailed_compound = self._get_complete_chembl_data(chembl_id)
            if detailed_compound:
                # Merge the detailed data with proper field mapping
                enriched_compound.update(detailed_compound)
                self.logger.info(f"After ChEMBL enrichment:")
                self.logger.info(f"  - Formula: {enriched_compound.get('molecular_formula')}")
                self.logger.info(f"  - Weight: {enriched_compound.get('molecular_weight')}")
                self.logger.info(f"  - SMILES: {enriched_compound.get('smiles')}")
                self.logger.info(f"  - PubChem CID: {enriched_compound.get('pubchem_cid')}")
            
            # STEP 2: Extract PubChem CID from cross-references if not already present
            if not enriched_compound.get('pubchem_cid'):
                self.logger.info("Step 2: Extracting PubChem CID from cross-references...")
                pubchem_cid = self._extract_pubchem_cid_from_xrefs(chembl_id)
                if pubchem_cid:
                    enriched_compound['pubchem_cid'] = pubchem_cid
                    self.logger.info(f"✅ Found PubChem CID from cross-references: {pubchem_cid}")
            
            # STEP 3: Try PubChem enrichment for any missing data
            missing_data = self._identify_missing_data(enriched_compound)
            if missing_data:
                self.logger.info(f"Step 3: Missing data detected: {missing_data}")
                self.logger.info("Attempting PubChem enrichment...")
                
                pubchem_data = self._get_pubchem_data_with_fallback(enriched_compound)
                
                if pubchem_data:
                    self.logger.info(f"PubChem data retrieved: {list(pubchem_data.keys())}")
                    
                    # Fill missing molecular formula
                    if not enriched_compound.get('molecular_formula') and pubchem_data.get('MolecularFormula'):
                        enriched_compound['molecular_formula'] = pubchem_data['MolecularFormula']
                        self.logger.info(f"✅ Added molecular formula from PubChem: {pubchem_data['MolecularFormula']}")
                    
                    # Fill missing molecular weight
                    if not enriched_compound.get('molecular_weight') and pubchem_data.get('MolecularWeight'):
                        try:
                            enriched_compound['molecular_weight'] = float(pubchem_data['MolecularWeight'])
                            self.logger.info(f"✅ Added molecular weight from PubChem: {pubchem_data['MolecularWeight']}")
                        except (ValueError, TypeError):
                            self.logger.warning(f"Could not convert molecular weight: {pubchem_data['MolecularWeight']}")
                    
                    # Fill missing PubChem CID
                    if not enriched_compound.get('pubchem_cid') and pubchem_data.get('CID'):
                        enriched_compound['pubchem_cid'] = str(pubchem_data['CID'])
                        self.logger.info(f"✅ Added PubChem CID: {pubchem_data['CID']}")
                    
                    # Fill missing SMILES
                    if not enriched_compound.get('smiles') and pubchem_data.get('CanonicalSMILES'):
                        enriched_compound['smiles'] = pubchem_data['CanonicalSMILES']
                        self.logger.info(f"✅ Added SMILES from PubChem: {pubchem_data['CanonicalSMILES']}")
                    
                    # Add additional PubChem data
                    if pubchem_data.get('IUPACName'):
                        enriched_compound['iupac_name'] = pubchem_data['IUPACName']
                    if pubchem_data.get('InChI'):
                        enriched_compound['inchi'] = pubchem_data['InChI']
                    if pubchem_data.get('InChIKey'):
                        enriched_compound['inchi_key'] = pubchem_data['InChIKey']
                else:
                    self.logger.warning(f"Could not retrieve PubChem data for {chembl_id}")
            
            # STEP 4: Get bioactivities count
            try:
                bioactivities = self.chembl_connector.get_bioactivities(chembl_id, limit=1)
                enriched_compound['bioactivities_count'] = len(bioactivities) if bioactivities else 0
            except Exception as e:
                self.logger.error(f"Error getting bioactivities for {chembl_id}: {e}")
                enriched_compound['bioactivities_count'] = 0
            
            # STEP 5: Final validation and cleanup
            enriched_compound = self._validate_and_clean_compound_data(enriched_compound)
            
            # Log final state
            self.logger.info(f"Final enriched data for {chembl_id}:")
            self.logger.info(f"  - Formula: {enriched_compound.get('molecular_formula')}")
            self.logger.info(f"  - Weight: {enriched_compound.get('molecular_weight')}")
            self.logger.info(f"  - SMILES: {enriched_compound.get('smiles')}")
            self.logger.info(f"  - PubChem CID: {enriched_compound.get('pubchem_cid')}")
            self.logger.info(f"  - Bioactivities: {enriched_compound.get('bioactivities_count')}")
            
            return enriched_compound
            
        except Exception as e:
            self.logger.error(f"Error enriching compound data for {chembl_id}: {e}")
            return compound
    
    def _get_complete_chembl_data(self, chembl_id: str) -> Optional[Dict]:
        """
        Get complete ChEMBL data with proper structure parsing - NEW METHOD
        """
        try:
            self.logger.info(f"Fetching complete ChEMBL data for {chembl_id}")
            
            # Get the complete compound data
            compound_data = self.chembl_connector.get_compound_with_enriched_data(chembl_id)
            
            if not compound_data:
                self.logger.warning(f"No complete ChEMBL data found for {chembl_id}")
                return None
            
            # Parse the structure properly - fix for molecular formula extraction
            parsed_data = {}
            
            # Handle molecular formula - check multiple possible locations
            if compound_data.get('molecular_formula'):
                parsed_data['molecular_formula'] = compound_data['molecular_formula']
            elif compound_data.get('molecule_chembl_id') and compound_data.get('molecule_structures'):
                # Try to extract from molecule_structures
                structures = compound_data.get('molecule_structures', {})
                if structures.get('molecular_formula'):
                    parsed_data['molecular_formula'] = structures['molecular_formula']
            
            # Handle molecular weight
            if compound_data.get('molecular_weight'):
                try:
                    parsed_data['molecular_weight'] = float(compound_data['molecular_weight'])
                except (ValueError, TypeError):
                    self.logger.warning(f"Could not parse molecular weight: {compound_data.get('molecular_weight')}")
            
            # Handle SMILES
            if compound_data.get('smiles'):
                parsed_data['smiles'] = compound_data['smiles']
            elif compound_data.get('molecule_structures', {}).get('canonical_smiles'):
                parsed_data['smiles'] = compound_data['molecule_structures']['canonical_smiles']
            
            # Handle other fields
            if compound_data.get('pref_name'):
                parsed_data['pref_name'] = compound_data['pref_name']
            
            # Extract PubChem CID from cross-references
            if compound_data.get('cross_references'):
                for xref in compound_data['cross_references']:
                    if xref.get('xref_src') == 'PubChem' and xref.get('xref_id'):
                        parsed_data['pubchem_cid'] = str(xref['xref_id'])
                        break
            
            self.logger.info(f"Parsed ChEMBL data: {list(parsed_data.keys())}")
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"Error getting complete ChEMBL data for {chembl_id}: {e}")
            return None
    
    def _extract_pubchem_cid_from_xrefs(self, chembl_id: str) -> Optional[str]:
        """
        Extract PubChem CID from ChEMBL cross-references - NEW METHOD
        """
        try:
            self.logger.info(f"Extracting PubChem CID from cross-references for {chembl_id}")
            
            # Get cross-references specifically
            xrefs = self.chembl_connector.get_compound_cross_references(chembl_id)
            
            if not xrefs:
                self.logger.info(f"No cross-references found for {chembl_id}")
                return None
            
            # Look for PubChem references
            for xref in xrefs:
                if xref.get('xref_src') == 'PubChem' and xref.get('xref_id'):
                    pubchem_cid = str(xref['xref_id'])
                    self.logger.info(f"Found PubChem CID in cross-references: {pubchem_cid}")
                    return pubchem_cid
            
            self.logger.info(f"No PubChem CID found in cross-references for {chembl_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting PubChem CID from cross-references for {chembl_id}: {e}")
            return None
    
    def _identify_missing_data(self, compound: Dict) -> List[str]:
        """
        Identify what data is missing from the compound - NEW METHOD
        """
        missing = []
        
        if not compound.get('molecular_formula'):
            missing.append('molecular_formula')
        if not compound.get('molecular_weight'):
            missing.append('molecular_weight')
        if not compound.get('smiles'):
            missing.append('smiles')
        if not compound.get('pubchem_cid'):
            missing.append('pubchem_cid')
        
        return missing
    
    def _get_pubchem_data_with_fallback(self, compound: Dict) -> Optional[Dict]:
        """
        Get PubChem data using multiple search strategies with better fallback - ENHANCED METHOD
        """
        try:
            chembl_id = compound.get('chembl_id')
            self.logger.info(f"Searching PubChem for {chembl_id}")
            
            # Strategy 1: Use existing PubChem CID if available
            pubchem_cid = compound.get('pubchem_cid')
            if pubchem_cid:
                self.logger.info(f"Strategy 1: Using existing PubChem CID: {pubchem_cid}")
                pubchem_data = self.pubchem_connector.get_compound_by_cid(pubchem_cid)
                if pubchem_data:
                    self.logger.info(f"✅ Found PubChem data by CID: {pubchem_cid}")
                    return pubchem_data
            
            # Strategy 2: Search by compound name
            pref_name = compound.get('pref_name')
            if pref_name:
                self.logger.info(f"Strategy 2: Searching PubChem by name: {pref_name}")
                pubchem_data = self.pubchem_connector.search_by_name(pref_name)
                if pubchem_data:
                    self.logger.info(f"✅ Found PubChem data by name: CID {pubchem_data.get('CID')}")
                    return pubchem_data
            
            # Strategy 3: Search by SMILES
            smiles = compound.get('smiles')
            if smiles:
                self.logger.info(f"Strategy 3: Searching PubChem by SMILES: {smiles}")
                pubchem_data = self.pubchem_connector.search_by_smiles(smiles)
                if pubchem_data:
                    self.logger.info(f"✅ Found PubChem data by SMILES: CID {pubchem_data.get('CID')}")
                    return pubchem_data
            
            # Strategy 4: Search by InChI if available
            inchi = compound.get('inchi')
            if inchi:
                self.logger.info(f"Strategy 4: Searching PubChem by InChI")
                pubchem_data = self.pubchem_connector.search_by_inchi(inchi)
                if pubchem_data:
                    self.logger.info(f"✅ Found PubChem data by InChI: CID {pubchem_data.get('CID')}")
                    return pubchem_data
            
            # Strategy 5: Search by molecular formula (if we have it)
            mol_formula = compound.get('molecular_formula')
            if mol_formula:
                self.logger.info(f"Strategy 5: Searching PubChem by molecular formula: {mol_formula}")
                pubchem_data = self.pubchem_connector.search_by_formula(mol_formula)
                if pubchem_data:
                    self.logger.info(f"✅ Found PubChem data by formula: CID {pubchem_data.get('CID')}")
                    return pubchem_data
            
            # Strategy 6: Try alternative names or synonyms from ChEMBL
            synonyms = compound.get('synonyms', [])
            for synonym in synonyms[:3]:  # Try first 3 synonyms
                if synonym and synonym != pref_name:
                    self.logger.info(f"Strategy 6: Searching PubChem by synonym: {synonym}")
                    pubchem_data = self.pubchem_connector.search_by_name(synonym)
                    if pubchem_data:
                        self.logger.info(f"✅ Found PubChem data by synonym: CID {pubchem_data.get('CID')}")
                        return pubchem_data
            
            self.logger.warning(f"Could not find PubChem data for {chembl_id} using any strategy")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting PubChem data for {compound.get('chembl_id')}: {e}")
            return None
    
    def _validate_and_clean_compound_data(self, compound: Dict) -> Dict:
        """
        Validate and clean compound data - NEW METHOD
        """
        try:
            # Ensure all required fields are present
            required_fields = ['chembl_id', 'pref_name', 'molecular_formula', 'molecular_weight', 'smiles', 'pubchem_cid']
            for field in required_fields:
                if field not in compound:
                    compound[field] = None
            
            # Clean and validate molecular weight
            if compound.get('molecular_weight'):
                try:
                    compound['molecular_weight'] = float(compound['molecular_weight'])
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid molecular weight: {compound.get('molecular_weight')}")
                    compound['molecular_weight'] = None
            
            # Clean PubChem CID
            if compound.get('pubchem_cid'):
                compound['pubchem_cid'] = str(compound['pubchem_cid'])
            
            # Ensure bioactivities_count is an integer
            if compound.get('bioactivities_count') is None:
                compound['bioactivities_count'] = 0
            
            return compound
            
        except Exception as e:
            self.logger.error(f"Error validating compound data: {e}")
            return compound
    
    def _store_compounds(self, compounds: List[Dict]):
        """
        Store compounds in database with enhanced error handling and proper sync - ENHANCED METHOD
        """
        try:
            stored_count = 0
            for compound in compounds:
                try:
                    # Prepare compound data for database
                    compound_data = {
                        'chembl_id': compound.get('chembl_id'),
                        'pubchem_cid': compound.get('pubchem_cid'),
                        'smiles': compound.get('smiles'),
                        'molecular_formula': compound.get('molecular_formula'),
                        'molecular_weight': compound.get('molecular_weight'),
                        'pref_name': compound.get('pref_name'),
                        'bioactivities_count': compound.get('bioactivities_count', 0)
                    }
                    
                    # Remove None values but keep empty strings and 0 values
                    compound_data = {k: v for k, v in compound_data.items() if v is not None}
                    
                    # Ensure we have the required fields
                    if not compound_data.get('chembl_id'):
                        self.logger.warning(f"Skipping compound without ChEMBL ID")
                        continue
                    
                    # Check if compound already exists
                    existing_compound = self.db.get_compound_by_chembl_id(compound_data['chembl_id'])
                    
                    if existing_compound:
                        # Update existing compound
                        self.logger.info(f"Updating existing compound {compound_data['chembl_id']}")
                        success = self.db.update_compound(compound_data['chembl_id'], compound_data)
                        if success:
                            self.logger.info(f"✅ Updated compound {compound_data['chembl_id']}")
                            stored_count += 1
                        else:
                            self.logger.warning(f"❌ Failed to update compound {compound_data['chembl_id']}")
                    else:
                        # Insert new compound
                        self.logger.info(f"Inserting new compound {compound_data['chembl_id']}")
                        compound_id = self.db.insert_compound(compound_data)
                        if compound_id:
                            self.logger.info(f"✅ Stored compound {compound_data['chembl_id']} with ID {compound_id}")
                            stored_count += 1
                        else:
                            self.logger.warning(f"❌ Failed to store compound {compound_data['chembl_id']}")
                            
                except Exception as e:
                    self.logger.error(f"Error storing individual compound {compound.get('chembl_id')}: {e}")
                    continue
            
            self.logger.info(f"Successfully stored/updated {stored_count}/{len(compounds)} compounds")
            
            # Force database sync if available
            if hasattr(self.db, 'sync'):
                self.db.sync()
                self.logger.info("Database sync completed")
                
        except Exception as e:
            self.logger.error(f"Error storing compounds: {e}")
    
    def get_compound_by_chembl_id(self, chembl_id: str) -> Optional[Dict]:
        """
        Get compound by ChEMBL ID, fetch from API if not in database - ENHANCED METHOD
        """
        try:
            self.logger.info(f"Getting compound {chembl_id}")
            
            # Try database first
            if self.db:
                compound = self.db.get_compound_by_chembl_id(chembl_id)
                if compound:
                    self.logger.info(f"Found compound {chembl_id} in database")
                    return compound
            
            # If not in database, fetch from APIs
            self.logger.info(f"Compound {chembl_id} not in database, fetching from APIs...")
            compound = self.chembl_connector.get_compound_with_enriched_data(chembl_id)
            
            if compound:
                self.logger.info(f"Retrieved compound {chembl_id} from ChEMBL")
                # Enrich with additional data
                enriched = self._enrich_compound_data(compound)
                
                # Store in database if available
                if enriched and self.db:
                    self._store_compounds([enriched])
                
                return enriched
            
            self.logger.warning(f"Compound {chembl_id} not found in any source")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting compound {chembl_id}: {e}")
            return None
    
    def get_enrichment_status(self, chembl_id: str) -> Dict:
        """
        Get the enrichment status of a compound - NEW METHOD
        """
        try:
            compound = self.get_compound_by_chembl_id(chembl_id)
            if not compound:
                return {'status': 'not_found', 'enrichment_score': 0}
            
            # Calculate enrichment score
            fields_to_check = ['molecular_formula', 'molecular_weight', 'smiles', 'pubchem_cid']
            enriched_fields = sum(1 for field in fields_to_check if compound.get(field))
            enrichment_score = (enriched_fields / len(fields_to_check)) * 100
            
            return {
                'status': 'found',
                'enrichment_score': enrichment_score,
                'enriched_fields': enriched_fields,
                'total_fields': len(fields_to_check),
                'missing_fields': [field for field in fields_to_check if not compound.get(field)]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting enrichment status for {chembl_id}: {e}")
            return {'status': 'error', 'error': str(e)}

# Test the data agent directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test the data agent
    agent = DataAgent()
    
    print("Testing DataAgent with complete fixes...")
    print("=" * 50)
    
    # Test 1: Basic compound query
    print("\n1. Testing basic compound query...")
    result = agent.process_compound_query("aspirin", limit=2)
    
    if result['success']:
        compounds = result['data']['compounds']
        print(f"✅ Found {len(compounds)} compounds")
        
        for compound in compounds:
            print(f"\nCompound: {compound.get('chembl_id')}")
            print(f"  Name: {compound.get('pref_name')}")
            print(f"  Formula: {compound.get('molecular_formula')}")
            print(f"  Weight: {compound.get('molecular_weight')}")
            print(f"  PubChem CID: {compound.get('pubchem_cid')}")
            print(f"  SMILES: {compound.get('smiles')}")
            print(f"  Bioactivities: {compound.get('bioactivities_count')}")
            
            # Test enrichment status
            enrichment = agent.get_enrichment_status(compound.get('chembl_id'))
            print(f"  Enrichment Score: {enrichment.get('enrichment_score', 0):.1f}%")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 2: Individual compound retrieval
    print("\n2. Testing individual compound retrieval...")
    compound = agent.get_compound_by_chembl_id("CHEMBL25")
    if compound:
        print(f"✅ Retrieved compound {compound.get('chembl_id')}")
        print(f"  Enrichment: {agent.get_enrichment_status('CHEMBL25')}")
    else:
        print("❌ Could not retrieve compound")
    
    print("\n" + "=" * 50)
    print("Testing complete!")
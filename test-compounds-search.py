# test_integration.py
import requests
import json
import time

def test_api_integration():
    """Test the complete API integration"""
    base_url = "http://localhost:5001"
    
    print("🧪 Testing MediAgent API Integration...")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print("❌ Health check failed")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Search compounds
    print("\n2. Testing compound search...")
    search_data = {
        "query": "aspirin",
        "limit": 3
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/compounds/search",
            json=search_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                compounds = data.get('data', {}).get('compounds', [])
                print(f"✅ Search successful - Found {len(compounds)} compounds")
                
                # Display compound details
                for i, compound in enumerate(compounds):
                    print(f"\n   Compound {i+1}:")
                    print(f"   ChEMBL ID: {compound.get('chembl_id')}")
                    print(f"   Name: {compound.get('pref_name')}")
                    print(f"   Molecular Formula: {compound.get('molecular_formula')}")
                    print(f"   Molecular Weight: {compound.get('molecular_weight')}")
                    print(f"   PubChem CID: {compound.get('pubchem_cid')}")
                    print(f"   SMILES: {compound.get('smiles')}")
                    print(f"   Bioactivities: {compound.get('bioactivities_count', 0)}")
                    
                    # Check for null values
                    if not compound.get('molecular_formula'):
                        print("   ⚠️  Molecular formula is missing")
                    if not compound.get('pubchem_cid'):
                        print("   ⚠️  PubChem CID is missing")
                
                return True
            else:
                print(f"❌ Search failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Search request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Search error: {e}")
        return False

def test_specific_compound():
    """Test getting a specific compound"""
    base_url = "http://localhost:5001"
    
    print("\n3. Testing specific compound retrieval...")
    
    # Test with aspirin ChEMBL ID
    chembl_id = "CHEMBL25"
    
    try:
        response = requests.get(f"{base_url}/api/v1/compounds/{chembl_id}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                compound = data.get('data', {})
                print(f"✅ Compound retrieval successful")
                print(f"   ChEMBL ID: {compound.get('chembl_id')}")
                print(f"   Name: {compound.get('pref_name')}")
                print(f"   Molecular Formula: {compound.get('molecular_formula')}")
                print(f"   Molecular Weight: {compound.get('molecular_weight')}")
                print(f"   PubChem CID: {compound.get('pubchem_cid')}")
                
                # Check data completeness
                if compound.get('molecular_formula') and compound.get('pubchem_cid'):
                    print("✅ All key data fields are present")
                    return True
                else:
                    print("⚠️  Some data fields are missing")
                    return False
            else:
                print(f"❌ Compound retrieval failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Compound request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Compound retrieval error: {e}")
        return False

def test_database_stats():
    """Test database statistics"""
    base_url = "http://localhost:5001"
    
    print("\n4. Testing database statistics...")
    
    try:
        response = requests.get(f"{base_url}/api/v1/database/stats")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data.get('data', {})
                print(f"✅ Database stats retrieved")
                print(f"   Total compounds: {stats.get('total_compounds')}")
                print(f"   Total bioactivities: {stats.get('total_bioactivities')}")
                print(f"   Recent compounds (24h): {stats.get('compounds_added_24h')}")
                return True
            else:
                print(f"❌ Database stats failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Database stats request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Database stats error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting API Integration Tests...")
    
    # Wait a bit for server to be ready
    time.sleep(2)
    
    # Run all tests
    results = []
    results.append(test_api_integration())
    results.append(test_specific_compound())
    results.append(test_database_stats())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"✅ Passed: {sum(results)}/{len(results)} tests")
    
    if all(results):
        print("🎉 All tests passed! Your API is working correctly.")
        print("\n💡 Key improvements made:")
        print("   - Fixed molecular formula extraction from ChEMBL API")
        print("   - Added PubChem CID lookup from cross-references")
        print("   - Enhanced error handling and data validation")
        print("   - Added fallback to PubChem for missing data")
        print("   - Improved response format for n8n workflow")
    else:
        print("❌ Some tests failed. Check the logs above for details.")
        
    print("\n🔧 To run this test:")
    print("   python test_integration.py")
    print("\n📝 To test with curl:")
    print('   curl -X POST http://localhost:5001/api/v1/compounds/search \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"query": "aspirin", "limit": 3}\'')
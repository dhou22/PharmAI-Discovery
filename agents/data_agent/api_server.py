# Updated Flask API (api_server.py)
from flask import Flask, request, jsonify
from flask_cors import CORS
from data_agent import DataAgent
import logging
import os

app = Flask(__name__)
CORS(app)

# Initialize with your database connection
data_agent = DataAgent()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'MediAgent Data Agent',
        'version': '1.0.0'
    })

@app.route('/api/v1/compounds/search', methods=['POST'])
def search_compounds():
    """Search compounds endpoint with optional AI analysis"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        limit = data.get('limit', 10)
        include_ai_analysis = data.get('include_ai_analysis', False)
        
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        # Use the enhanced data agent with AI analysis option
        result = data_agent.process_compound_query(query, limit, include_ai_analysis)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'compounds': [],
                'compounds_found': 0,
                'query': query if 'query' in locals() else ''
            }
        }), 500

@app.route('/api/v1/compounds/<chembl_id>', methods=['GET'])
def get_compound(chembl_id):
    """Get compound by ChEMBL ID"""
    try:
        compound = data_agent.get_compound_by_chembl_id(chembl_id)
        
        if not compound:
            return jsonify({'error': 'Compound not found'}), 404
        
        return jsonify({
            'success': True,
            'data': compound
        })
    
    except Exception as e:
        logger.error(f"Get compound error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/compounds/analyze/<chembl_id>', methods=['POST'])
def analyze_compound(chembl_id):
    """Analyze a specific compound using AI"""
    try:
        compound = data_agent.get_compound_by_chembl_id(chembl_id)
        
        if not compound:
            return jsonify({
                'success': False,
                'error': 'Compound not found'
            }), 404
        
        analysis = data_agent.analyze_compound_with_ai(compound)
        
        return jsonify({
            'success': True,
            'compound': compound,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Analyze compound error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/model/info', methods=['GET'])
def get_model_info():
    """Get current Ollama model information"""
    try:
        model_info = data_agent.get_ollama_model_info()
        return jsonify({
            'success': True,
            'model_info': model_info
        })
    except Exception as e:
        logger.error(f"Get model info error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/status', methods=['GET'])
def get_system_status():
    """Get comprehensive system status"""
    try:
        status = data_agent.get_system_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f"Get system status error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/compounds/batch-analyze', methods=['POST'])
def batch_analyze_compounds():
    """Analyze multiple compounds with AI"""
    try:
        data = request.get_json()
        chembl_ids = data.get('chembl_ids', [])
        
        if not chembl_ids:
            return jsonify({
                'success': False,
                'error': 'chembl_ids parameter is required'
            }), 400
        
        results = []
        for chembl_id in chembl_ids:
            try:
                compound = data_agent.get_compound_by_chembl_id(chembl_id)
                if compound:
                    analysis = data_agent.analyze_compound_with_ai(compound)
                    results.append({
                        'chembl_id': chembl_id,
                        'compound': compound,
                        'analysis': analysis
                    })
                else:
                    results.append({
                        'chembl_id': chembl_id,
                        'error': 'Compound not found'
                    })
            except Exception as e:
                results.append({
                    'chembl_id': chembl_id,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'total_processed': len(results)
        })
        
    except Exception as e:
        logger.error(f"Batch analyze error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/compounds/search-and-analyze', methods=['POST'])
def search_and_analyze_compounds():
    """Search compounds and automatically analyze them with AI"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        limit = data.get('limit', 5)  # Lower default for AI analysis
        
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        # Always include AI analysis for this endpoint
        result = data_agent.process_compound_query(query, limit, include_ai_analysis=True)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Search and analyze error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'compounds': [],
                'compounds_found': 0,
                'query': query if 'query' in locals() else ''
            }
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

# Add a route to test AI functionality


if __name__ == '__main__':
    # Log startup information
    logger.info("Starting MediAgent Data Agent API Server...")
    logger.info(f"Ollama Host: {data_agent.ollama_host}")
    logger.info(f"Configured Model: {data_agent.ollama_model}")
    logger.info(f"Current Model: {data_agent.current_model}")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
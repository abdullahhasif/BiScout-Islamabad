from flask import Blueprint, request, jsonify
import traceback
import sys

# Try importing LlamaIndex implementation first
try:
    from services.llamaindex_rag import process_query as llamaindex_process_query
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    print("Warning: LlamaIndex RAG implementation not available. Will use simple RAG fallback.")
    LLAMAINDEX_AVAILABLE = False
except Exception as e:
    print(f"Error importing LlamaIndex: {e}")
    LLAMAINDEX_AVAILABLE = False

# Always import the simple implementation as a fallback
from services.simple_rag import process_query as simple_process_query

bp = Blueprint('queries', __name__, url_prefix='/api/queries')

@bp.route('/', methods=['POST'])
def handle_query():
    """Process a natural language query"""
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({'error': 'Query is required'}), 400
    
    query_text = data['query']
    
    # Try LlamaIndex RAG first if available
    if LLAMAINDEX_AVAILABLE:
        try:
            result = llamaindex_process_query(query_text)
            if result.get('success', False):
                return jsonify(result)
        except Exception as e:
            print(f"LlamaIndex RAG failed: {e}")
            print(traceback.format_exc())
            # Fall through to simple RAG
    
    # Use simple RAG as fallback
    try:
        print("Using simple RAG fallback...")
        result = simple_process_query(query_text)
        return jsonify(result)
    except Exception as e:
        print(f"Simple RAG also failed: {e}")
        print(traceback.format_exc())
        return jsonify({
            'error': 'Failed to process query',
            'success': False,
            'response': "I'm sorry, I encountered an error processing your question. Please try again later."
        }), 500 
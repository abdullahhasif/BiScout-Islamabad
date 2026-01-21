"""
BioScout Islamabad - Biodiversity Monitoring Platform

This is the main application entry point that initializes the Flask application,
registers blueprints, and configures services.
"""

import os
import logging
from flask import Flask, render_template, send_from_directory, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from config import Config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """
    Create and configure the Flask application
    
    Returns:
        Flask: Configured Flask application instance
    """
    logger.info("Initializing BioScout Islamabad application")
    
    # Create Flask app
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(Config)
    
    # Enable CORS for API endpoints
    CORS(app)
    
    # Register blueprints for API routes
    logger.info("Registering API blueprints")
    register_blueprints(app)
    
    # Initialize services
    logger.info("Initializing services")
    initialize_services()
    
    # Create required directories
    logger.info("Creating required directories")
    create_directories(app)
    
    # Register routes
    register_routes(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    logger.info("Application initialization complete")
    return app

def register_blueprints(app):
    """Register API blueprints"""
    try:
        from routes.observation_routes import bp as observation_bp
        from routes.query_routes import bp as query_bp
        from routes.user_routes import bp as user_bp
        
        app.register_blueprint(observation_bp)
        app.register_blueprint(query_bp)
        app.register_blueprint(user_bp)
    except Exception as e:
        logger.error(f"Error registering blueprints: {e}")
        raise

def initialize_services():
    """Initialize required services"""
    # Initialize the RAG updater service
    try:
        from services.rag_updater import start_update_thread
        logger.info("Initializing RAG updater service")
        # Service is started automatically when imported
    except ImportError:
        logger.warning("RAG updater service not available. Continuing without it.")
    except Exception as e:
        logger.error(f"Error initializing RAG updater service: {e}")

def create_directories(app):
    """Create required directories for the application"""
    try:
        # Create upload directory if it doesn't exist
        upload_folder = app.config.get('UPLOAD_FOLDER', os.path.join(app.static_folder, 'uploads'))
        os.makedirs(upload_folder, exist_ok=True)
        
        # Sample data directory - ensure it exists
        sample_dir = os.path.join('static', 'images', 'samples')
        os.makedirs(sample_dir, exist_ok=True)
        
        # Knowledge data directory
        knowledge_dir = os.path.join('data', 'knowledge_files')
        os.makedirs(knowledge_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        raise

def register_routes(app):
    """Register main application routes"""
    @app.route('/')
    def index():
        """Render the main application page"""
        return render_template('index.html')

    @app.route('/static/<path:path>')
    def serve_static(path):
        """Serve static files"""
        return send_from_directory('static', path)

    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        return {'status': 'healthy', 'version': '1.0.0'}

def register_error_handlers(app):
    """Register error handlers for the application"""
    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 Not Found errors"""
        logger.warning(f"Resource not found: {str(e)}")
        return jsonify({'error': 'Resource not found', 'status': 404}), 404

    @app.errorhandler(500)
    def server_error(e):
        """Handle 500 Internal Server Error"""
        logger.error(f"Internal server error: {str(e)}")
        return jsonify({'error': 'Internal server error', 'status': 500}), 500

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Print startup message
    print("=" * 50)
    print("BioScout Islamabad - Biodiversity Monitoring Platform")
    print("=" * 50)
    print("API Endpoints:")
    print("  - /api/observations")
    print("  - /api/queries")
    print("  - /api/users")
    print("=" * 50)
    
    # Start the Flask app
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=True) 
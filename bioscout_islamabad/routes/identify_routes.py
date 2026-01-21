"""
Routes for species identification functionality
"""

from flask import Blueprint, request, jsonify, render_template
import os
import uuid
from werkzeug.utils import secure_filename
from services.inaturalist_service import inaturalist_service
from services.image_service import get_exif_data, get_coordinates_from_exif
from config import Config

bp = Blueprint('identify', __name__, url_prefix='/api')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@bp.route('/identify', methods=['POST'])
def identify_species():
    """
    Identify a species from an uploaded image using iNaturalist API
    """
    # Check if image is part of the request
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image part'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Create upload directory if it doesn't exist
        upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), Config.UPLOAD_FOLDER)
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save the uploaded file
        filename = secure_filename(str(uuid.uuid4()) + '_' + file.filename)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        try:
            # Get species identification from iNaturalist
            identification_result = inaturalist_service.identify_species_from_upload(file_path)
            
            if not identification_result['success']:
                return jsonify({
                    'success': False,
                    'message': identification_result.get('message', 'Failed to identify species'),
                    'image_url': f'/static/uploads/{filename}'
                }), 400
            
            # Extract location from image metadata
            exif_data = get_exif_data(file_path)
            coordinates = get_coordinates_from_exif(exif_data)
            
            # Prepare the response
            response_data = {
                'success': True,
                'image_url': f'/static/uploads/{filename}',
                'identification_text': identification_result.get('identification_text', ''),
                'top_result': identification_result.get('top_result', {}),
                'results': identification_result.get('results', []),
                'coordinates': coordinates
            }
            
            return jsonify(response_data), 200
            
        except Exception as e:
            # Log the error
            import logging
            logging.error(f"Error in species identification: {str(e)}")
            
            return jsonify({
                'success': False,
                'message': f"Error identifying species: {str(e)}",
                'image_url': f'/static/uploads/{filename}'
            }), 500
    
    return jsonify({'success': False, 'message': 'Invalid file type'}), 400

# Add a route for the identification page
def register_page_routes(app):
    """Register page routes with the Flask app"""
    
    @app.route('/identify')
    def identify_page():
        """Render the species identification page"""
        return render_template('identify.html') 
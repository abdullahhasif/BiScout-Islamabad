from flask import Blueprint, request, jsonify
import os
import uuid
from werkzeug.utils import secure_filename
from models.observation import Observation
from services.species_identification_service import get_species_from_image
from services.inaturalist_service import inaturalist_service
from services.image_service import get_exif_data, get_coordinates_from_exif
from services.data_persistence_service import is_plant_species
from config import Config

# Import the RAG updater service
try:
    from services.rag_updater import process_new_observation
    RAG_UPDATER_AVAILABLE = True
except ImportError:
    print("Warning: RAG updater service not available. Real-time RAG updates will be disabled.")
    RAG_UPDATER_AVAILABLE = False

bp = Blueprint('observations', __name__, url_prefix='/api/observations')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@bp.route('/', methods=['GET'])
def get_observations():
    """Get all observations or filter by query params"""
    species = request.args.get('species')
    location = request.args.get('location')
    category = request.args.get('category')  # 'plant', 'animal', or all
    species_type = request.args.get('type')  # Optional: filter by species type (mammal, bird, tree, etc.)
    
    # First get observations based on primary filters
    if species:
        observations = Observation.find_by_species(species)
    elif location:
        observations = Observation.find_by_location(location)
    elif category:
        observations = Observation.find_by_category(category)
    else:
        observations = Observation.find_all()
    
    # Apply additional type filter if specified
    if species_type and species_type != 'all':
        # Filter observations by species type
        filtered_observations = []
        for obs in observations:
            # Get the species type from the observation if available
            obs_species_type = obs.get('species_type')
            
            # If the observation already has a species_type and it matches, add it
            if obs_species_type and obs_species_type.lower() == species_type.lower():
                filtered_observations.append(obs)
            # Otherwise use the legacy detection approach
            else:
                species_name = obs.get('species_name', '').lower()
                if species_type == 'mammal' and any(x in species_name for x in ['deer', 'leopard', 'fox', 'bear', 'boar']):
                    filtered_observations.append(obs)
                elif species_type == 'bird' and any(x in species_name for x in ['bird', 'duck', 'griffon', 'owl']):
                    filtered_observations.append(obs)
                elif species_type == 'reptile' and any(x in species_name for x in ['snake', 'cobra', 'lizard']):
                    filtered_observations.append(obs)
                elif species_type == 'amphibian' and any(x in species_name for x in ['frog', 'toad']):
                    filtered_observations.append(obs)
                elif species_type == 'fish' and any(x in species_name for x in ['fish', 'carp']):
                    filtered_observations.append(obs)
                elif species_type == 'tree' and any(x in species_name for x in ['pine', 'cedar', 'oak', 'palm']):
                    filtered_observations.append(obs)
                elif species_type == 'plant' and is_plant_species(species_name) and not any(x in species_name for x in ['pine', 'cedar', 'oak', 'palm']):
                    filtered_observations.append(obs)
        
        observations = filtered_observations
    
    return jsonify({'observations': observations})

@bp.route('/', methods=['POST'])
def create_observation():
    """Create a new observation"""
    # Check if image is part of the request
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Create upload directory if it doesn't exist
        upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), Config.UPLOAD_FOLDER)
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save the uploaded file
        filename = secure_filename(str(uuid.uuid4()) + '_' + file.filename)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Choose identification method: iNaturalist or legacy
        use_inaturalist = Config.ENABLE_AUTO_IDENTIFICATION and request.form.get('use_ai', 'true').lower() == 'true'
        
        if use_inaturalist:
            # Get species identification from iNaturalist
            identification_result = inaturalist_service.identify_species_from_upload(file_path)
            ai_success = identification_result['success']
            ai_identification_text = identification_result.get('identification_text', '')
            
            # Extract species name and category from identification result
            species_name = None
            category = None
            species_type = None
            
            if ai_success and identification_result.get('top_result'):
                top_result = identification_result['top_result']
                species_name = top_result.get('common_name')
                if not species_name or species_name == 'Unknown':
                    species_name = top_result.get('scientific_name')
                
                # Set category and species_type based on identification
                if top_result.get('is_plant'):
                    category = 'plant'
                    species_type = 'plant'
                    # Further refine plant types
                    if any(x in species_name.lower() for x in ['tree', 'pine', 'cedar', 'oak', 'palm']):
                        species_type = 'tree'
                    elif any(x in species_name.lower() for x in ['grass', 'sedge']):
                        species_type = 'grass'
                    elif any(x in species_name.lower() for x in ['flower', 'lily', 'rose', 'daisy']):
                        species_type = 'flower'
                elif top_result.get('is_animal'):
                    category = 'animal'
                    species_type = top_result.get('rank')
        else:
            # Use legacy species identification
            ai_result = get_species_from_image(file_path)
            ai_success = ai_result['success']
            ai_identification_text = ai_result['result'] if ai_success else 'Failed to identify species'
            
            # For legacy method, we don't automatically extract species name or category
            species_name = None
            category = None
            species_type = None
        
        # Extract location from image metadata
        exif_data = get_exif_data(file_path)
        coordinates = get_coordinates_from_exif(exif_data)
        
        # Get form data, using AI results as fallback when needed
        user_id = request.form.get('user_id', 'anonymous')
        form_species_name = request.form.get('species_name')
        
        # Use form data over AI if provided
        if form_species_name:
            species_name = form_species_name
        
        # Get other form data
        location_name = request.form.get('location')
        notes = request.form.get('notes', '')
        
        # If coordinates not found in EXIF, check if provided in form
        if not coordinates and request.form.get('coordinates'):
            try:
                import json
                coordinates = json.loads(request.form.get('coordinates'))
            except:
                pass
        
        # Get new form fields, using AI results as fallback
        date_observed = request.form.get('date_observed')
        quantity = request.form.get('quantity', 1)
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            quantity = 1
        
        # Override category and species_type with form data if provided
        form_category = request.form.get('category')
        if form_category:
            category = form_category
            
        form_species_type = request.form.get('species_type')
        if form_species_type:
            species_type = form_species_type
            
        habitat_type = request.form.get('habitat')
        
        # Create and save observation
        observation = Observation(
            user_id=user_id,
            species_name=species_name,
            location=location_name,
            coordinates=coordinates,
            image_url=f'/static/uploads/{filename}',
            notes=notes,
            ai_identification=ai_identification_text,
            date_observed=date_observed,
            quantity=quantity,
            category=category,
            habitat_type=habitat_type,
            species_type=species_type
        )
        
        observation_id = observation.save()
        
        # The new observation should be saved now with an ID, so we can retrieve it
        saved_observation = Observation.find_by_id(observation_id)
        
        # Update the RAG system with the new observation if the updater is available
        if RAG_UPDATER_AVAILABLE and saved_observation:
            print(f"Updating RAG system with new observation {observation_id}")
            process_new_observation(saved_observation)
        
        # Prepare the response
        response_data = {
            'success': True,
            'observation_id': observation_id,
            'image_url': f'/static/uploads/{filename}',
            'ai_identification': ai_identification_text,
            'species_name': species_name,
            'category': category,
            'species_type': species_type,
            'coordinates': coordinates,
            'rag_updated': RAG_UPDATER_AVAILABLE
        }
        
        # Include the full identification results if available
        if use_inaturalist and ai_success:
            response_data['identification_results'] = identification_result.get('results')
        
        return jsonify(response_data), 201
    
    return jsonify({'error': 'Invalid file type'}), 400

@bp.route('/<observation_id>', methods=['GET'])
def get_observation(observation_id):
    """Get a specific observation by ID"""
    observation = Observation.find_by_id(observation_id)
    if observation:
        return jsonify({'observation': observation})
    return jsonify({'error': 'Observation not found'}), 404 
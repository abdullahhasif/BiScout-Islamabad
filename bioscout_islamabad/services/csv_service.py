"""
Data Persistence Service

This module handles data persistence using CSV files as a lightweight database.
It provides operations for saving and retrieving observations, knowledge documents, and user data.

This would be better implemented with a proper database in a production environment.
"""

import os
import csv
import json
import logging
from datetime import datetime
from config import Config

# Set up logging
logger = logging.getLogger(__name__)

# Base directory for CSV files
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), Config.DATABASE_DIR)
os.makedirs(DATA_DIR, exist_ok=True)

# CSV file paths
ANIMALS_CSV = os.path.join(DATA_DIR, 'animals_observations.csv')
PLANTS_CSV = os.path.join(DATA_DIR, 'plants_observations.csv')
KNOWLEDGE_CSV = os.path.join(DATA_DIR, 'knowledge_base.csv')
USERS_CSV = os.path.join(DATA_DIR, 'users.csv')

# CSV headers
OBSERVATION_HEADERS = ['id', 'user_id', 'species_name', 'date_observed', 'location',
                       'coordinates', 'image_url', 'notes', 'ai_identification', 'created_at',
                       'category', 'quantity', 'habitat_type', 'species_type']
KNOWLEDGE_HEADERS = ['id', 'title', 'content', 'source', 'category', 'region', 'created_at']
USER_HEADERS = ['id', 'username', 'email', 'full_name', 'created_at']

# Plant species detection keywords
PLANT_KEYWORDS = [
    'pine', 'cedar', 'tree', 'plant', 'flower', 'shrub', 'herb',
    'amaltas', 'neem', 'mulberry', 'date palm', 'shisham',
    'bottle brush', 'tulsi', 'blue pine', 'chir pine', 'himalayan cedar',
    'fern', 'grass', 'vine', 'bush', 'conifer', 'oak', 'maple'
]

# Create files if they don't exist
def initialize_csv_files():
    """Initialize CSV files with headers if they don't exist."""
    files_to_check = [
        (ANIMALS_CSV, OBSERVATION_HEADERS),
        (PLANTS_CSV, OBSERVATION_HEADERS),
        (KNOWLEDGE_CSV, KNOWLEDGE_HEADERS),
        (USERS_CSV, USER_HEADERS)
    ]
    
    for file_path, headers in files_to_check:
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                logger.info(f"Created file: {file_path}")
            except Exception as e:
                logger.error(f"Error creating {file_path}: {e}")

# Generate a simple ID
def generate_id():
    """
    Generate a unique ID based on timestamp.
    
    Returns:
        str: Unique ID
    """
    return str(int(datetime.now().timestamp() * 1000))

# Helper function to read CSV into list of dicts
def read_csv_to_dicts(file_path, headers):
    """
    Read CSV file into a list of dictionaries.
    
    Args:
        file_path (str): Path to the CSV file
        headers (list): List of column headers
        
    Returns:
        list: List of dictionaries, each representing a row
    """
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return []
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except UnicodeDecodeError:
        # Try with a different encoding if UTF-8 fails
        try:
            with open(file_path, 'r', newline='', encoding='latin-1') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            logger.error(f"Error reading {file_path} with fallback encoding: {e}")
            return []
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return []

# Helper function to write list of dicts to CSV
def write_dicts_to_csv(file_path, data, headers):
    """
    Write list of dictionaries to CSV file.
    
    Args:
        file_path (str): Path to the CSV file
        data (list): List of dictionaries to write
        headers (list): List of column headers
    """
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        logger.debug(f"Successfully wrote {len(data)} rows to {file_path}")
    except Exception as e:
        logger.error(f"Error writing to {file_path}: {e}")
        raise

# Determine if a species is a plant or animal
def is_plant_species(species_name):
    """
    Determine if a species name is a plant based on keywords.
    
    Args:
        species_name (str): Name of the species
        
    Returns:
        bool: True if likely a plant, False otherwise
    """
    if not species_name:
        return False
    
    species_lower = species_name.lower()
    return any(keyword in species_lower for keyword in PLANT_KEYWORDS)

# CSV Observation Operations
def save_observation(observation_data):
    """
    Save observation to appropriate CSV file based on species type.
    
    Args:
        observation_data (dict): Observation data to save
        
    Returns:
        str: ID of the saved observation
    """
    observation_id = generate_id()
    
    try:
        # Convert complex data types to strings
        if 'coordinates' in observation_data and observation_data['coordinates']:
            observation_data['coordinates'] = json.dumps(observation_data['coordinates'])
        
        # Add timestamps
        observation_data['created_at'] = datetime.now().isoformat()
        observation_data['id'] = observation_id
        
        # Determine file based on species type
        if is_plant_species(observation_data.get('species_name')):
            target_file = PLANTS_CSV
        else:
            target_file = ANIMALS_CSV
        
        # Read existing data
        observations = read_csv_to_dicts(target_file, OBSERVATION_HEADERS)
        
        # Append new data
        observations.append(observation_data)
        
        # Save back to CSV
        write_dicts_to_csv(target_file, observations, OBSERVATION_HEADERS)
        logger.info(f"Saved observation {observation_id} to {target_file}")
        
        return observation_id
    except Exception as e:
        logger.error(f"Error saving observation: {e}")
        return None

def find_observation_by_id(observation_id):
    """
    Find observation by ID in both CSV files.
    
    Args:
        observation_id (str): ID of the observation to find
        
    Returns:
        dict or None: Observation data if found, None otherwise
    """
    if not observation_id:
        return None
        
    # Check plants first
    try:
        observations = read_csv_to_dicts(PLANTS_CSV, OBSERVATION_HEADERS)
        
        for obs in observations:
            if obs['id'] == observation_id:
                process_coordinates(obs)
                return obs
        
        # Then check animals
        observations = read_csv_to_dicts(ANIMALS_CSV, OBSERVATION_HEADERS)
        
        for obs in observations:
            if obs['id'] == observation_id:
                process_coordinates(obs)
                return obs
    except Exception as e:
        logger.error(f"Error finding observation by ID: {e}")
    
    return None

def process_coordinates(observation):
    """
    Convert string coordinates to list if needed.
    
    Args:
        observation (dict): Observation data with potential coordinates
        
    Returns:
        dict: Updated observation with processed coordinates
    """
    if not observation:
        return observation
        
    try:
        if 'coordinates' in observation and observation['coordinates']:
            try:
                observation['coordinates'] = json.loads(observation['coordinates'])
            except json.JSONDecodeError:
                pass
    except Exception as e:
        logger.error(f"Error processing coordinates: {e}")
        
    return observation

def find_all_observations():
    """
    Find all observations from both plants and animals CSV files.
    
    Returns:
        list: List of all observations
    """
    try:
        plant_observations = read_csv_to_dicts(PLANTS_CSV, OBSERVATION_HEADERS)
        animal_observations = read_csv_to_dicts(ANIMALS_CSV, OBSERVATION_HEADERS)
        
        # Combine and convert coordinates
        all_observations = plant_observations + animal_observations
        for obs in all_observations:
            process_coordinates(obs)
        
        return all_observations
    except Exception as e:
        logger.error(f"Error finding all observations: {e}")
        return []

def find_all_plant_observations():
    """
    Find all plant observations.
    
    Returns:
        list: List of plant observations
    """
    try:
        observations = read_csv_to_dicts(PLANTS_CSV, OBSERVATION_HEADERS)
        for obs in observations:
            process_coordinates(obs)
        return observations
    except Exception as e:
        logger.error(f"Error finding plant observations: {e}")
        return []

def find_all_animal_observations():
    """
    Find all animal observations.
    
    Returns:
        list: List of animal observations
    """
    try:
        observations = read_csv_to_dicts(ANIMALS_CSV, OBSERVATION_HEADERS)
        for obs in observations:
            process_coordinates(obs)
        return observations
    except Exception as e:
        logger.error(f"Error finding animal observations: {e}")
        return []

def find_observations_by_species(species_name):
    """
    Find observations by species name (case-insensitive).
    
    Args:
        species_name (str): Name of the species to search for
        
    Returns:
        list: List of matching observations
    """
    if not species_name:
        return []
        
    try:
        species_name = species_name.lower()
        results = []
        
        # Determine which file(s) to search based on the species name
        if is_plant_species(species_name):
            observations = read_csv_to_dicts(PLANTS_CSV, OBSERVATION_HEADERS)
        else:
            observations = read_csv_to_dicts(ANIMALS_CSV, OBSERVATION_HEADERS)
        
        # Filter by species name
        for obs in observations:
            obs_species = obs.get('species_name', '').lower()
            if species_name in obs_species:
                process_coordinates(obs)
                results.append(obs)
        
        return results
    except Exception as e:
        logger.error(f"Error finding observations by species: {e}")
        return []

def find_observations_by_location(location_name):
    """
    Find observations by location (case-insensitive).
    
    Args:
        location_name (str): Location to search for
        
    Returns:
        list: List of matching observations
    """
    if not location_name:
        return []
        
    try:
        location_name = location_name.lower()
        results = []
        
        # Search in both files
        for file_path in [PLANTS_CSV, ANIMALS_CSV]:
            observations = read_csv_to_dicts(file_path, OBSERVATION_HEADERS)
            
            for obs in observations:
                obs_location = obs.get('location', '').lower()
                if location_name in obs_location:
                    process_coordinates(obs)
                    results.append(obs)
        
        return results
    except Exception as e:
        logger.error(f"Error finding observations by location: {e}")
        return []

def find_observations_by_category(category):
    """
    Find observations by category (plant or animal).
    
    Args:
        category (str): Category to filter by ('plant' or 'animal')
        
    Returns:
        list: List of matching observations
    """
    try:
        if category.lower() == 'plant':
            return find_all_plant_observations()
        elif category.lower() == 'animal':
            return find_all_animal_observations()
        else:
            return find_all_observations()
    except Exception as e:
        logger.error(f"Error finding observations by category: {e}")
        return []

# CSV Knowledge Base Operations
def save_knowledge_document(document_data):
    """
    Save knowledge document to CSV.
    
    Args:
        document_data (dict): Knowledge document data to save
        
    Returns:
        str: ID of the saved document
    """
    try:
        document_id = generate_id()
        
        # Add timestamps
        document_data['created_at'] = datetime.now().isoformat()
        document_data['id'] = document_id
        
        # Read existing data
        documents = read_csv_to_dicts(KNOWLEDGE_CSV, KNOWLEDGE_HEADERS)
        
        # Append new data
        documents.append(document_data)
        
        # Save back to CSV
        write_dicts_to_csv(KNOWLEDGE_CSV, documents, KNOWLEDGE_HEADERS)
        
        return document_id
    except Exception as e:
        logger.error(f"Error saving knowledge document: {e}")
        return None

def find_knowledge_document_by_id(document_id):
    """
    Find knowledge document by ID.
    
    Args:
        document_id (str): ID of the document to find
        
    Returns:
        dict or None: Document data if found, None otherwise
    """
    if not document_id:
        return None
        
    try:
        documents = read_csv_to_dicts(KNOWLEDGE_CSV, KNOWLEDGE_HEADERS)
        
        for doc in documents:
            if doc['id'] == document_id:
                return doc
    except Exception as e:
        logger.error(f"Error finding knowledge document: {e}")
    
    return None

def search_knowledge_documents(query):
    """
    Search knowledge documents by query terms (case-insensitive).
    
    Args:
        query (str): Search query
        
    Returns:
        list: List of matching documents
    """
    if not query:
        return []
        
    try:
        documents = read_csv_to_dicts(KNOWLEDGE_CSV, KNOWLEDGE_HEADERS)
        query = query.lower()
        
        results = []
        for doc in documents:
            # Check in each searchable field
            if (query in doc.get('title', '').lower() or
                query in doc.get('content', '').lower() or
                query in doc.get('region', '').lower() or
                query in doc.get('category', '').lower()):
                # Avoid duplicates
                if doc not in results:
                    results.append(doc)
        
        return results
    except Exception as e:
        logger.error(f"Error searching knowledge documents: {e}")
        return []

# CSV User Operations
def save_user(user_data):
    """
    Save user to CSV.
    
    Args:
        user_data (dict): User data to save
        
    Returns:
        str: ID of the saved user
    """
    try:
        user_id = generate_id()
        
        # Add timestamps
        user_data['created_at'] = datetime.now().isoformat()
        user_data['id'] = user_id
        
        # Read existing data
        users = read_csv_to_dicts(USERS_CSV, USER_HEADERS)
        
        # Append new data
        users.append(user_data)
        
        # Save back to CSV
        write_dicts_to_csv(USERS_CSV, users, USER_HEADERS)
        
        return user_id
    except Exception as e:
        logger.error(f"Error saving user: {e}")
        return None

def find_user_by_username(username):
    """
    Find user by username.
    
    Args:
        username (str): Username to search for
        
    Returns:
        dict or None: User data if found, None otherwise
    """
    if not username:
        return None
        
    try:
        users = read_csv_to_dicts(USERS_CSV, USER_HEADERS)
        
        for user in users:
            if user['username'] == username:
                return user
    except Exception as e:
        logger.error(f"Error finding user by username: {e}")
    
    return None

def find_user_by_id(user_id):
    """
    Find user by ID.
    
    Args:
        user_id (str): ID of the user to find
        
    Returns:
        dict or None: User data if found, None otherwise
    """
    if not user_id:
        return None
        
    try:
        users = read_csv_to_dicts(USERS_CSV, USER_HEADERS)
        
        for user in users:
            if user['id'] == user_id:
                return user
    except Exception as e:
        logger.error(f"Error finding user by ID: {e}")
    
    return None

# Initialize CSV files on module import
initialize_csv_files() 
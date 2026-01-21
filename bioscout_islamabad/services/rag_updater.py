"""
RAG Updater Service - Ensures real-time synchronization between observations and RAG knowledge base.
"""

import os
import time
from typing import Dict, Optional, List
import threading
import json
from datetime import datetime

# Try to import LlamaIndex components
try:
    from llama_index.core import Document
    from llama_index.core import VectorStoreIndex
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    print("LlamaIndex not available for RAG updater")

# Flag to track if the index needs updating
needs_update = False
# Lock for thread safety
update_lock = threading.Lock()
# Time of last update
last_update_time = time.time()
# Update cooldown period in seconds (to prevent excessive updates)
UPDATE_COOLDOWN = 60  

# Path for observation logs that track which observations are added to the knowledge base
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
OBSERVATION_LOG_PATH = os.path.join(DATA_DIR, 'observation_index_log.json')

def init_observation_log():
    """Initialize the observation log if it doesn't exist"""
    if not os.path.exists(OBSERVATION_LOG_PATH):
        with open(OBSERVATION_LOG_PATH, 'w') as f:
            json.dump({
                'indexed_observations': [],
                'last_update': datetime.now().isoformat()
            }, f)

def get_indexed_observations() -> List[str]:
    """Get list of observation IDs already indexed"""
    if not os.path.exists(OBSERVATION_LOG_PATH):
        init_observation_log()
        return []
    
    try:
        with open(OBSERVATION_LOG_PATH, 'r') as f:
            data = json.load(f)
            return data.get('indexed_observations', [])
    except Exception as e:
        print(f"Error reading observation log: {e}")
        return []

def log_indexed_observation(observation_id: str):
    """Add an observation ID to the log of indexed observations"""
    indexed_ids = get_indexed_observations()
    
    if observation_id in indexed_ids:
        return  # Already indexed
    
    indexed_ids.append(observation_id)
    
    try:
        with open(OBSERVATION_LOG_PATH, 'w') as f:
            json.dump({
                'indexed_observations': indexed_ids,
                'last_update': datetime.now().isoformat()
            }, f)
    except Exception as e:
        print(f"Error updating observation log: {e}")

def signal_update_needed():
    """Signal that the RAG system needs to be updated"""
    global needs_update, last_update_time
    
    with update_lock:
        needs_update = True
        current_time = time.time()
        
        # If cooldown period has passed, update immediately
        if current_time - last_update_time > UPDATE_COOLDOWN:
            print("Update cooldown passed, updating RAG index immediately")
            update_rag_index()
        else:
            print(f"Update needed, but waiting for cooldown ({UPDATE_COOLDOWN}s)")

def update_rag_index():
    """Update the RAG index with new observations"""
    global needs_update, last_update_time
    
    with update_lock:
        if not needs_update:
            return
        
        # Reset flags
        needs_update = False
        last_update_time = time.time()
        
        print("Updating RAG index with new observations...")
        
        if LLAMAINDEX_AVAILABLE:
            _update_llamaindex()
        else:
            _update_simple_rag()
        
        print("RAG index update completed")

def observation_to_document(observation: Dict) -> Optional[Dict]:
    """Convert an observation to a document format for indexing"""
    if not observation:
        return None
    
    # Create detailed content about the observation
    content = f"""
    Biodiversity Observation in Islamabad, Pakistan:
    Species: {observation.get('species_name', 'Unknown')}
    Location: {observation.get('location', 'Unknown location')}
    Date Observed: {observation.get('date_observed', 'Unknown date')}
    
    Notes: {observation.get('notes', 'No notes provided')}
    """
    
    # Add AI identification if available
    if observation.get('ai_identification'):
        content += f"\nAI Species Identification: {observation.get('ai_identification')}"
    
    # Add GPS coordinates if available
    if observation.get('coordinates'):
        lat = observation['coordinates'][1] if len(observation['coordinates']) > 1 else 'Unknown'
        long = observation['coordinates'][0] if len(observation['coordinates']) > 0 else 'Unknown'
        content += f"\nGPS Coordinates: Latitude {lat}, Longitude {long}"
    
    # Add category (plant/animal)
    if 'plant' in str(observation.get('species_name', '')).lower() or any(plant_type in str(observation.get('species_name', '')).lower() for plant_type in ['tree', 'pine', 'cedar', 'neem', 'amaltas']):
        content += "\nCategory: Plant"
    else:
        content += "\nCategory: Animal"
    
    # Set metadata
    metadata = {
        'source': 'user_observation',
        'species': observation.get('species_name', 'Unknown'),
        'location': observation.get('location', 'Unknown location'),
        'date': observation.get('date_observed', 'Unknown date'),
        'observation_id': observation.get('id', 'unknown')
    }
    
    if LLAMAINDEX_AVAILABLE:
        return Document(text=content, metadata=metadata)
    else:
        return {
            'content': content,
            'metadata': metadata
        }

def _update_llamaindex():
    """Update the LlamaIndex RAG system with new observations"""
    if not LLAMAINDEX_AVAILABLE:
        print("LlamaIndex not available, skipping update")
        return
    
    try:
        # Import here to avoid circular imports
        from services.llamaindex_rag import vector_index, initialize_index
        from models.observation import Observation
        
        # Get all observations
        all_observations = Observation.find_all()
        
        # Get IDs of already indexed observations
        indexed_ids = get_indexed_observations()
        
        # Filter for new observations only
        new_observations = [obs for obs in all_observations if obs.get('id') not in indexed_ids]
        
        if not new_observations:
            print("No new observations to add to LlamaIndex")
            return
        
        print(f"Adding {len(new_observations)} new observations to LlamaIndex")
        
        # Convert to documents
        documents = []
        for obs in new_observations:
            doc = observation_to_document(obs)
            if doc and isinstance(doc, Document):
                documents.append(doc)
                log_indexed_observation(obs.get('id'))
        
        if not documents:
            print("No valid documents to add to index")
            return
        
        # If index doesn't exist, initialize it
        if vector_index is None:
            initialize_index()
            return  # Initialization will include all observations
        
        # Update existing index with new documents
        vector_index.insert_nodes(vector_index.build_index_from_documents(documents))
        print(f"Successfully added {len(documents)} documents to LlamaIndex")
        
    except Exception as e:
        print(f"Error updating LlamaIndex: {e}")

def _update_simple_rag():
    """Update the simple RAG system - primarily just logs which observations have been processed"""
    try:
        # Import here to avoid circular imports
        from models.observation import Observation
        
        # Get all observations
        all_observations = Observation.find_all()
        
        # Get IDs of already processed observations
        indexed_ids = get_indexed_observations()
        
        # Filter for new observations only
        new_observations = [obs for obs in all_observations if obs.get('id') not in indexed_ids]
        
        if not new_observations:
            print("No new observations to process for simple RAG")
            return
        
        print(f"Processing {len(new_observations)} new observations for simple RAG")
        
        # Just log them as processed (simple RAG fetches observations dynamically)
        for obs in new_observations:
            log_indexed_observation(obs.get('id'))
        
    except Exception as e:
        print(f"Error updating simple RAG log: {e}")

def process_new_observation(observation_data: Dict):
    """Process a new observation and update the RAG system accordingly"""
    # Log the observation for indexing
    if observation_data and 'id' in observation_data:
        print(f"Processing new observation {observation_data['id']} for RAG")
        signal_update_needed()
    
# Initialize the log file when module is loaded
init_observation_log()

# Start a background thread to periodically check and update if needed
def start_update_thread():
    def update_thread_func():
        while True:
            with update_lock:
                if needs_update and time.time() - last_update_time > UPDATE_COOLDOWN:
                    update_rag_index()
            time.sleep(30)  # Check every 30 seconds
    
    thread = threading.Thread(target=update_thread_func, daemon=True)
    thread.start()
    print("RAG update background thread started")

# Start the background thread when module is imported
start_update_thread() 
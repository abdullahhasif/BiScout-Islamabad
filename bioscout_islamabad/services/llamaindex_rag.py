import os
import json
import openai
from typing import List, Dict
import importlib.util
import sys

# Check if numpy is available and try to provide helpful error message
try:
    import numpy
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: numpy not installed. LlamaIndex will not be available.")
except Exception as e:
    NUMPY_AVAILABLE = False
    print(f"Error with numpy: {e}")
    print("Run the fix_numpy.py script to resolve this issue.")

# Only try to import LlamaIndex components if numpy is available
LLAMAINDEX_AVAILABLE = False
if NUMPY_AVAILABLE:
    try:
        from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
        from llama_index.core import Settings
        from llama_index.llms.openai import OpenAI
        from llama_index.embeddings.openai import OpenAIEmbedding
        from llama_index.core.schema import Document
        LLAMAINDEX_AVAILABLE = True
    except ImportError as e:
        print(f"Warning: Error importing LlamaIndex: {e}")
        print("Make sure all LlamaIndex packages are installed.")
    except Exception as e:
        print(f"Error initializing LlamaIndex: {e}")
        print("Run the fix_numpy.py script to resolve compatibility issues.")

from config import Config
from models.observation import Observation

# Configure knowledge base directories
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
KNOWLEDGE_DIR = os.path.join(DATA_DIR, 'knowledge_files')

# Ensure directories exist
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

# Global index for reuse
vector_index = None


def initialize_index():
    """Initialize or reload the vector index"""
    global vector_index
    
    if not LLAMAINDEX_AVAILABLE:
        print("LlamaIndex is not available - cannot initialize index")
        return False
    
    try:
        # Configure LLM and embedding model
        llm = OpenAI(model="gpt-4", api_key=Config.OPENAI_API_KEY)
        embed_model = OpenAIEmbedding(api_key=Config.OPENAI_API_KEY)
        
        # Set up global settings
        Settings.llm = llm
        Settings.embed_model = embed_model
        
        # Check if we have knowledge files
        if os.path.exists(KNOWLEDGE_DIR) and any(os.listdir(KNOWLEDGE_DIR)):
            # Load existing knowledge files
            documents = SimpleDirectoryReader(KNOWLEDGE_DIR).load_data()
            print(f"Loaded {len(documents)} knowledge documents")
        else:
            # Create default knowledge if no files exist
            create_default_knowledge_files()
            documents = SimpleDirectoryReader(KNOWLEDGE_DIR).load_data()
            print(f"Created and loaded default knowledge files")
        
        # Add observation documents if available
        observation_documents = create_documents_from_observations()
        if observation_documents:
            documents.extend(observation_documents)
            print(f"Added {len(observation_documents)} observation documents to index")
        
        # Create index using the global settings
        vector_index = VectorStoreIndex.from_documents(documents)
        print("Vector index successfully initialized")
        return True
        
    except Exception as e:
        print(f"Error initializing vector index: {e}")
        print("Try running the fix_numpy.py script to resolve compatibility issues.")
        return False


def create_default_knowledge_files():
    """Create default knowledge files about Islamabad wildlife"""
    default_knowledge = [
        {
            "title": "Margalla Hills Biodiversity",
            "content": """
            Margalla Hills National Park is home to diverse wildlife including the common leopard, 
            barking deer, wild boar, rhesus macaque, and various bird species. The park is known for 
            its rich biodiversity with over 600 plant species, 250 bird species, 38 mammal species, 
            and 13 reptile species. Notable birds include the Egyptian vulture, Himalayan griffon, 
            laggar falcon, peregrine falcon, kestrel, Indian sparrow hawk, and spotted owlet.
            """,
            "source": "Islamabad Wildlife Management Board",
            "category": "Biodiversity",
            "region": "Margalla Hills"
        },
        {
            "title": "Rawal Lake Ecosystem",
            "content": """
            Rawal Lake is an artificial reservoir that provides water to Islamabad and Rawalpindi. 
            The lake hosts numerous migratory birds during winter, including mallards, pochards, 
            coots, and herons. Fish species include common carp, rohu, and mahseer. The surrounding 
            vegetation includes acacia, pine, and eucalyptus trees. The lake also supports various 
            reptiles such as monitor lizards and snakes.
            """,
            "source": "Pakistan Environmental Protection Agency",
            "category": "Aquatic Ecosystems",
            "region": "Rawal Lake"
        },
        {
            "title": "Threatened Species in Islamabad",
            "content": """
            Several species found in Islamabad are considered threatened or endangered, including the 
            Indian pangolin, smooth-coated otter, and Himalayan black bear. The Indian pangolin is 
            critically endangered due to poaching for its scales. Conservation efforts focus on 
            habitat protection, anti-poaching measures, and public awareness campaigns.
            """,
            "source": "IUCN Red List",
            "category": "Conservation",
            "region": "Islamabad"
        }
    ]
    
    # Write each knowledge item to a separate file
    for i, knowledge in enumerate(default_knowledge):
        filename = f"knowledge_{i+1}.txt"
        filepath = os.path.join(KNOWLEDGE_DIR, filename)
        
        with open(filepath, 'w') as f:
            f.write(f"# {knowledge['title']}\n\n")
            f.write(knowledge['content'].strip())
            f.write(f"\n\nSource: {knowledge['source']}")
            f.write(f"\nCategory: {knowledge['category']}")
            f.write(f"\nRegion: {knowledge['region']}")


def create_documents_from_observations() -> List[Document]:
    """Create document objects from observations for indexing"""
    if not LLAMAINDEX_AVAILABLE:
        print("LlamaIndex not available - cannot create documents")
        return []
        
    # Get list of indexed observation IDs from rag_updater if available
    indexed_ids = []
    try:
        from services.rag_updater import get_indexed_observations
        indexed_ids = get_indexed_observations()
        print(f"Found {len(indexed_ids)} already indexed observations")
    except ImportError:
        print("RAG updater not available, indexing all observations")
    
    observations = Observation.find_all()
    documents = []
    
    for obs in observations:
        obs_id = obs.get('id')
        # Skip already indexed observations if we have this information
        if indexed_ids and obs_id in indexed_ids:
            continue
            
        content = f"""
        Species: {obs.get('species_name', 'Unknown')}
        Location: {obs.get('location', 'Unknown location')}
        Date: {obs.get('date_observed', 'Unknown date')}
        Notes: {obs.get('notes', 'No notes provided')}
        """
        
        if obs.get('ai_identification'):
            content += f"\nAI Identification: {obs.get('ai_identification')}"
        
        metadata = {
            "source": "observation",
            "species": obs.get('species_name', 'Unknown'),
            "location": obs.get('location', 'Unknown location'),
            "date": obs.get('date_observed', 'Unknown date'),
            "id": obs_id
        }
        
        documents.append(Document(text=content, metadata=metadata))
        
        # Log observation as indexed if rag_updater is available
        try:
            from services.rag_updater import log_indexed_observation
            if obs_id:
                log_indexed_observation(obs_id)
        except ImportError:
            pass
    
    return documents


def update_index_with_observation(observation: Dict):
    """Update the vector index with a new observation"""
    if not LLAMAINDEX_AVAILABLE:
        print("LlamaIndex not available - cannot update index")
        return
    
    global vector_index
    
    if vector_index is None:
        # If index doesn't exist, initialize it with all observations
        print("Index not initialized, initializing with all observations")
        initialize_index()
        return
    
    try:
        # Create document from observation
        content = f"""
        Species: {observation.get('species_name', 'Unknown')}
        Location: {observation.get('location', 'Unknown location')}
        Date: {observation.get('date_observed', 'Unknown date')}
        Notes: {observation.get('notes', 'No notes provided')}
        """
        
        if observation.get('ai_identification'):
            content += f"\nAI Identification: {observation.get('ai_identification')}"
        
        metadata = {
            "source": "observation",
            "species": observation.get('species_name', 'Unknown'),
            "location": observation.get('location', 'Unknown location'),
            "date": observation.get('date_observed', 'Unknown date'),
            "id": observation.get('id', 'unknown')
        }
        
        document = Document(text=content, metadata=metadata)
        
        # Update index with new document
        vector_index.insert_nodes(vector_index.build_index_from_documents([document]))
        print(f"Added observation {observation.get('id')} to vector index")
        
        # Log as indexed
        try:
            from services.rag_updater import log_indexed_observation
            if observation.get('id'):
                log_indexed_observation(observation.get('id'))
        except ImportError:
            pass
            
    except Exception as e:
        print(f"Error updating index with observation: {e}")


def process_query(query_text: str) -> Dict:
    """Process a natural language query using the LlamaIndex RAG system"""
    global vector_index
    
    # Check if LlamaIndex is available
    if not LLAMAINDEX_AVAILABLE:
        print("LlamaIndex not available - falling back to simple RAG")
        try:
            from services.simple_rag import process_query as simple_process_query
            return simple_process_query(query_text)
        except Exception as e:
            print(f"Error with fallback to simple RAG: {e}")
            return {
                "response": "I'm sorry, I'm having trouble processing your query. Please try running fix_numpy.py script to fix compatibility issues.",
                "success": False
            }
    
    # Initialize index if it doesn't exist
    if vector_index is None:
        success = initialize_index()
        if not success:
            print("Failed to initialize index - falling back to simple RAG")
            try:
                from services.simple_rag import process_query as simple_process_query
                return simple_process_query(query_text)
            except Exception as e:
                print(f"Error with fallback to simple RAG: {e}")
                return {
                    "response": "I'm having trouble accessing the knowledge base. Please try again later.",
                    "success": False
                }
    
    try:
        # Retrieve observations that might be relevant
        key_terms = extract_key_terms(query_text)
        observation_results = []
        
        for term in key_terms:
            species_observations = Observation.find_by_species(term)
            location_observations = Observation.find_by_location(term)
            observation_results.extend(species_observations)
            observation_results.extend(location_observations)
        
        # Create query engine
        query_engine = vector_index.as_query_engine()
        
        # Query the index
        response = query_engine.query(query_text)
        
        return {
            "response": response.response,
            "success": True,
            "observations": format_observations(observation_results)
        }
    except Exception as e:
        print(f"Error processing query with LlamaIndex: {e}")
        # Fallback to direct LLM response with observations only
        return fallback_response(query_text, observation_results)


def extract_key_terms(query):
    """Extract potential species or location names from query"""
    # This is a simplified implementation - in production would use NER or similar
    # Known locations in Islamabad
    locations = ["margalla hills", "rawal lake", "shakarparian", "daman-e-koh", 
                 "pir sohawa", "trail", "islamabad"]
    
    # Animal categories
    categories = ["bird", "birds", "mammal", "mammals", "reptile", "reptiles", 
                  "amphibian", "amphibians", "fish"]
    
    terms = []
    query_lower = query.lower()
    
    # Check for locations
    for location in locations:
        if location in query_lower:
            terms.append(location)
    
    # Check for categories
    for category in categories:
        if category in query_lower:
            terms.append(category)
    
    return terms


def fallback_response(query, observations):
    """Generate a fallback response using direct OpenAI call with observations only"""
    try:
        client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Create a simple context from observations
        context = "Based on our records:\n"
        for obs in observations[:5]:  # Limit to 5
            context += f"- {obs.get('species_name', 'Unknown species')} observed at {obs.get('location', 'Unknown location')}\n"
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Fallback to a cheaper model
            messages=[
                {"role": "system", "content": f"You are a biodiversity expert in Islamabad, Pakistan. Answer based only on these observations: {context}"},
                {"role": "user", "content": query}
            ],
            max_tokens=300
        )
        
        return {
            "response": response.choices[0].message.content,
            "success": True,
            "observations": format_observations(observations),
            "note": "Using fallback response method"
        }
    except Exception as e:
        print(f"Error in fallback response: {e}")
        return {
            "response": "I'm sorry, I'm having trouble processing your question at the moment. Please try again later.",
            "success": False,
            "observations": format_observations(observations)
        }


def format_observations(observations):
    """Format observations for map display"""
    formatted = []
    for obs in observations:
        if 'coordinates' in obs and obs['coordinates']:
            formatted.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': obs['coordinates']
                },
                'properties': {
                    'id': str(obs.get('id', 'unknown')),
                    'species': obs.get('species_name', 'Unknown'),
                    'date': obs.get('date_observed', ''),
                    'location': obs.get('location', ''),
                    'notes': obs.get('notes', '')
                }
            })
    return formatted


# Initialize the index when module is imported
initialize_index() 
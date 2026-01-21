"""
Simple RAG implementation using only OpenAI, without LlamaIndex.
This serves as a fallback if there are compatibility issues with LlamaIndex.
"""

import os
import json
import openai
from typing import List, Dict
from config import Config
from models.observation import Observation

# Configure knowledge base directories
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
KNOWLEDGE_DIR = os.path.join(DATA_DIR, 'knowledge_files')

def load_knowledge_files():
    """Load all knowledge files from the knowledge directory"""
    knowledge_content = []
    
    if os.path.exists(KNOWLEDGE_DIR):
        for filename in os.listdir(KNOWLEDGE_DIR):
            if filename.endswith('.txt'):
                file_path = os.path.join(KNOWLEDGE_DIR, filename)
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        knowledge_content.append({
                            'filename': filename,
                            'content': content
                        })
                except Exception as e:
                    print(f"Error reading knowledge file {filename}: {e}")
    
    return knowledge_content

def extract_key_terms(query):
    """Extract potential species or location names from query"""
    # Known locations in Islamabad
    locations = ["margalla hills", "rawal lake", "shakarparian", "daman-e-koh", 
                 "pir sohawa", "trail", "islamabad", "f-9 park", "zoo"]
    
    # Animal categories
    categories = ["bird", "birds", "mammal", "mammals", "reptile", "reptiles", 
                  "amphibian", "amphibians", "fish"]
    
    # Plant categories and types
    plant_terms = ["plant", "plants", "tree", "trees", "flower", "flowers", 
                   "shrub", "shrubs", "herb", "herbs", "pine", "cedar", 
                   "medicinal", "garden", "forest", "conifer", "invasive", 
                   "native", "vegetation", "botanical", "flora"]
    
    # Specific plant species in Islamabad
    plant_species = ["chir pine", "blue pine", "himalayan cedar", "deodar", 
                     "phulai", "acacia", "shisham", "siris", "wild date palm", 
                     "date palm", "amaltas", "jacaranda", "bottle brush", 
                     "silver oak", "paper mulberry", "ficus", "ber", "kau", 
                     "sanatha", "ajwain", "mint", "sage", "aloe vera", "tulsi", 
                     "arjun", "neem"]
    
    terms = []
    query_lower = query.lower()
    
    # Check for locations
    for location in locations:
        if location in query_lower:
            terms.append(location)
    
    # Check for animal categories
    for category in categories:
        if category in query_lower:
            terms.append(category)
    
    # Check for plant-related terms
    for term in plant_terms:
        if term in query_lower:
            terms.append(term)
    
    # Check for specific plant species
    for species in plant_species:
        if species in query_lower:
            terms.append(species)
    
    return terms

def get_relevant_knowledge(query, knowledge_files):
    """Simple keyword matching to find relevant knowledge files"""
    query_lower = query.lower()
    terms = extract_key_terms(query)
    
    relevant_content = []
    
    # First check: Plant specific queries should prioritize plant knowledge
    if any(plant_term in query_lower for plant_term in ["plant", "tree", "flora", "vegetation"]):
        for knowledge in knowledge_files:
            if "plant" in knowledge['filename'].lower():
                relevant_content.append(knowledge['content'])
    
    # Then process regular term matching
    for knowledge in knowledge_files:
        content_lower = knowledge['content'].lower()
        
        # Check if any terms are in the content
        if any(term in content_lower for term in terms):
            if knowledge['content'] not in relevant_content:  # Avoid duplicates
                relevant_content.append(knowledge['content'])
            continue
            
        # Direct query keyword match
        words = query_lower.split()
        for word in words:
            if len(word) > 3 and word in content_lower:
                if knowledge['content'] not in relevant_content:  # Avoid duplicates
                    relevant_content.append(knowledge['content'])
                break
    
    return relevant_content

def get_relevant_observations(query):
    """Find observations relevant to the query"""
    key_terms = extract_key_terms(query)
    observations = []
    
    # Check for category-specific queries
    is_plant_query = any(plant_term in query.lower() for plant_term in [
        'plant', 'tree', 'flower', 'shrub', 'herb', 'botanical', 'flora', 'vegetation'
    ])
    
    is_animal_query = any(animal_term in query.lower() for animal_term in [
        'animal', 'mammal', 'bird', 'reptile', 'amphibian', 'fish', 'wildlife', 'fauna'
    ])
    
    # Get observations based on query category
    if is_plant_query and not is_animal_query:
        base_observations = Observation.find_plants()
    elif is_animal_query and not is_plant_query:
        base_observations = Observation.find_animals()
    else:
        # If general query or mentions both, search in all observations
        base_observations = Observation.find_all()
    
    # Check for specific species in the query (more precise than key terms)
    for obs in base_observations:
        species_name = obs.get('species_name', '').lower()
        if species_name and species_name in query.lower():
            # Direct species mention is highest priority
            if obs not in observations:
                observations.append(obs)
    
    # If no exact species matches, try key terms
    if not observations:
        # Look for specific mentions
        for term in key_terms:
            # Find by species first
            species_observations = []
            for obs in base_observations:
                species_name = obs.get('species_name', '').lower()
                if term in species_name and obs not in observations:
                    species_observations.append(obs)
            
            # If no species match, try finding by location
            if not species_observations:
                for obs in base_observations:
                    location = obs.get('location', '').lower()
                    if term in location and obs not in observations:
                        observations.append(obs)
            else:
                observations.extend(species_observations)
    
    # Limit to a reasonable number to avoid context length issues
    return observations[:10]

def build_context(query, knowledge_files, observations):
    """Build context from knowledge files and observations"""
    # Check for plant or animal focus
    is_plant_query = any(plant_term in query.lower() for plant_term in [
        'plant', 'tree', 'flower', 'shrub', 'herb', 'botanical', 'flora', 'vegetation'
    ])
    
    is_animal_query = any(animal_term in query.lower() for animal_term in [
        'animal', 'mammal', 'bird', 'reptile', 'amphibian', 'fish', 'wildlife', 'fauna'
    ])
    
    # Get relevant knowledge filtered by query type
    relevant_knowledge = []
    for knowledge in knowledge_files:
        content_lower = knowledge['content'].lower()
        
        # For plant queries, prioritize plant-focused content
        if is_plant_query and not is_animal_query:
            if 'plant' in content_lower or 'tree' in content_lower or 'botanical' in content_lower:
                relevant_knowledge.append(knowledge['content'])
                continue
        
        # For animal queries, prioritize animal-focused content
        elif is_animal_query and not is_plant_query:
            if 'animal' in content_lower or 'mammal' in content_lower or 'bird' in content_lower or 'wildlife' in content_lower:
                relevant_knowledge.append(knowledge['content'])
                continue
    
    # If no category-specific knowledge found, use standard relevance method
    if not relevant_knowledge:
        relevant_knowledge = get_relevant_knowledge(query, knowledge_files)
    
    context = ""
    
    if relevant_knowledge:
        context += "Knowledge Base Information:\n"
        for i, knowledge in enumerate(relevant_knowledge[:3]):  # Limit to top 3
            # Get first 300 characters to keep context manageable
            preview = knowledge[:1000].replace('\n\n', ' ').replace('\n', ' ')
            context += f"[{i+1}] {preview}...\n\n"
    
    if observations:
        context += "\nRecent Observations:\n"
        for i, obs in enumerate(observations[:5]):  # Limit to 5
            species = obs.get('species_name', 'Unknown species')
            location = obs.get('location', 'Unknown location')
            date = obs.get('date_observed', 'Unknown date')
            context += f"- {species} observed at {location} on {date}\n"
    
    return context

def process_query(query_text: str) -> Dict:
    """Process a query using a simple RAG approach"""
    try:
        # Load knowledge files
        knowledge_files = load_knowledge_files()
        if not knowledge_files:
            print("Warning: No knowledge files found")
        
        # Get relevant observations
        observations = get_relevant_observations(query_text)
        
        # Build context
        context = build_context(query_text, knowledge_files, observations)
        
        if not context:
            context = "No specific information found in our knowledge base."
        
        # Generate response using OpenAI
        client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"""You are a biodiversity expert specialized in the flora and fauna of Islamabad, Pakistan. 
                Answer questions based on the following context. If you don't know the answer based on the context, say so politely.
                
                Context:
                {context}"""},
                {"role": "user", "content": query_text}
            ],
            max_tokens=500
        )
        
        return {
            "response": response.choices[0].message.content,
            "success": True,
            "observations": format_observations(observations),
            "using_fallback": True
        }
    except Exception as e:
        print(f"Error in simple RAG: {e}")
        return {
            "response": "I'm sorry, I'm having trouble processing your question at the moment. Please try again later.",
            "success": False,
            "observations": []
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
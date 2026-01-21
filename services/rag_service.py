import os
import openai
import json
import traceback
from models.knowledge_base import KnowledgeDocument
from models.observation import Observation
from config import Config

# Check if we're in fallback mode (no valid API key)
USE_FALLBACK_MODE = False

def process_query(query):
    """Process user query using RAG system"""
    try:
        # Step 1: Retrieve relevant documents from knowledge base
        knowledge_results = KnowledgeDocument.search(query)
        
        # Step 2: Retrieve relevant observations
        observation_results = []
        # Extract potential species or location names from query
        key_terms = extract_key_terms(query)
        
        for term in key_terms:
            species_observations = Observation.find_by_species(term)
            location_observations = Observation.find_by_location(term)
            observation_results.extend(species_observations)
            observation_results.extend(location_observations)
        
        # Step 3: Build context from retrieved information
        context = build_context(knowledge_results, observation_results)
        
        # Step 4: Generate response using OpenAI or fallback
        response = generate_response(query, context)
        
        return {
            'response': response,
            'knowledge_sources': [doc['title'] for doc in knowledge_results],
            'observation_count': len(observation_results),
            'observations': format_observations(observation_results)
        }
    except Exception as e:
        print(f"Error in process_query: {e}")
        traceback.print_exc()
        return {
            'response': "I'm sorry, there was an error processing your query. Please try again.",
            'knowledge_sources': [],
            'observation_count': 0,
            'observations': []
        }

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

def build_context(knowledge_docs, observations):
    """Build context from retrieved documents and observations"""
    context = "Knowledge Base Information:\n"
    
    for doc in knowledge_docs[:3]:  # Limit to top 3 most relevant documents
        context += f"- {doc['title']} ({doc['source']}): {doc['content'][:300]}...\n\n"
    
    context += "\nRecent Observations:\n"
    for obs in observations[:5]:  # Limit to 5 most recent observations
        species = obs.get('species_name', 'Unknown species')
        location = obs.get('location', 'Unknown location')
        date = obs.get('date_observed', 'Unknown date')
        context += f"- {species} observed at {location} on {date}\n"
    
    return context

def generate_fallback_response(query, context):
    """Generate a fallback response based on the context without using OpenAI API"""
    global USE_FALLBACK_MODE
    USE_FALLBACK_MODE = True
    
    # Basic keyword matching for fallback responses
    query_lower = query.lower()
    
    # Extract key information from context
    species_mentioned = []
    locations_mentioned = []
    for line in context.split('\n'):
        if line.startswith('- ') and 'observed at' in line:
            species = line.split('observed at')[0].replace('- ', '').strip()
            location = line.split('observed at')[1].split('on')[0].strip()
            species_mentioned.append(species)
            locations_mentioned.append(location)
    
    # Build a simple response based on the query and available information
    if "bird" in query_lower or "birds" in query_lower:
        bird_species = [s for s in species_mentioned if "bird" in s.lower() or "duck" in s.lower() or "eagle" in s.lower()]
        if bird_species:
            return f"Based on our records, the following bird species have been observed in Islamabad: {', '.join(bird_species)}."
        else:
            return "I don't have specific information about birds in that area from our records."
    
    if "margalla" in query_lower:
        margalla_species = []
        for i, loc in enumerate(locations_mentioned):
            if "margalla" in loc.lower() and i < len(species_mentioned):
                margalla_species.append(species_mentioned[i])
        
        if margalla_species:
            return f"In Margalla Hills, these species have been recorded: {', '.join(margalla_species)}."
        else:
            return "Margalla Hills is known for its biodiversity, but I don't have specific observations in our current records."
    
    if "rawal" in query_lower or "lake" in query_lower:
        lake_species = []
        for i, loc in enumerate(locations_mentioned):
            if "rawal" in loc.lower() and i < len(species_mentioned):
                lake_species.append(species_mentioned[i])
        
        if lake_species:
            return f"At Rawal Lake, these species have been observed: {', '.join(lake_species)}."
        else:
            return "Rawal Lake is home to various species, but I don't have specific observations in our current records."
    
    # Default response if no specific matches
    if species_mentioned:
        return f"Based on our records, these species have been observed in Islamabad: {', '.join(species_mentioned[:3])}."
    else:
        return "I don't have specific information about that in our current records. You can try asking about birds, mammals, or specific locations like Margalla Hills or Rawal Lake."

def generate_response(query, context):
    """Generate response using OpenAI with context"""
    global USE_FALLBACK_MODE
    
    # First, check if we're already in fallback mode
    if USE_FALLBACK_MODE:
        return generate_fallback_response(query, context)
    
    # Try to use OpenAI
    api_key = Config.OPENAI_API_KEY
    
    # Basic API key validation check
    if "None" in api_key or not api_key or len(api_key) < 20:
        print("Invalid API key detected. Using fallback mode.")
        return generate_fallback_response(query, context)
    
    try:
        # Set up OpenAI with the API key
        openai.api_key = api_key
        
        # First try with the Turbo model
        try:
            response = openai.chat.completions.create(
                model="gpt-4-1106-preview",  # GPT-4 Turbo
                messages=[
                    {"role": "system", "content": f"""You are a biodiversity expert specialized in the flora and fauna of Islamabad, Pakistan. 
                    Answer questions based on the following context. If you don't know the answer based on the context, say so politely.
                    
                    Context:
                    {context}"""},
                    {"role": "user", "content": query}
                ],
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as model_error:
            print(f"Error with gpt-4-1106-preview: {model_error}")
            
            # Fallback to gpt-3.5-turbo if GPT-4 Turbo fails
            try:
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",  # Fallback to GPT-3.5
                    messages=[
                        {"role": "system", "content": f"""You are a biodiversity expert specialized in the flora and fauna of Islamabad, Pakistan. 
                        Answer questions based on the following context. If you don't know the answer based on the context, say so politely.
                        
                        Context:
                        {context}"""},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=500
                )
                return response.choices[0].message.content
            except Exception as fallback_error:
                print(f"Error with fallback model gpt-3.5-turbo: {fallback_error}")
                USE_FALLBACK_MODE = True
                return generate_fallback_response(query, context)
                
    except Exception as e:
        print(f"Error generating response: {e}")
        print(f"API Key (first 5 chars): {api_key[:5]}...")
        traceback.print_exc()
        USE_FALLBACK_MODE = True
        return generate_fallback_response(query, context)

def format_observations(observations):
    """Format observations for map display"""
    formatted = []
    for obs in observations:
        if 'coordinates' in obs and obs['coordinates']:
            try:
                formatted.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': obs['coordinates']
                    },
                    'properties': {
                        'id': str(obs.get('id', '')),
                        'species': obs.get('species_name', 'Unknown'),
                        'date': obs.get('date_observed', ''),
                        'location': obs.get('location', ''),
                        'notes': obs.get('notes', '')
                    }
                })
            except Exception as e:
                print(f"Error formatting observation: {e}")
    return formatted 
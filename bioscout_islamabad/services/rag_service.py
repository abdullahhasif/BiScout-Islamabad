import os
import openai
from models.knowledge_base import KnowledgeDocument
from models.observation import Observation
from config import Config

def process_query(query):
    """Process user query using RAG system"""
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
    
    # Step 4: Generate response using OpenAI
    response = generate_response(query, context)
    
    return {
        'response': response,
        'knowledge_sources': [doc['title'] for doc in knowledge_results],
        'observation_count': len(observation_results),
        'observations': format_observations(observation_results)
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

def generate_response(query, context):
    """Generate response using OpenAI with context"""
    api_key = Config.OPENAI_API_KEY
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4",
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
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I'm sorry, I encountered an error while processing your question. Please try again."

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
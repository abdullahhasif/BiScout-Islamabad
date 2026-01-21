import os
import requests
import base64
import traceback
from config import Config

# Flag for fallback mode
USE_FALLBACK_MODE = False

def get_species_from_image(image_path):
    """Identify species in an image using GPT-4 Vision API"""
    global USE_FALLBACK_MODE
    
    # If we already know we're in fallback mode, don't attempt API call
    if USE_FALLBACK_MODE:
        return generate_fallback_identification(image_path)
    
    api_key = Config.OPENAI_API_KEY
    
    # Basic API key validation check
    if "None" in api_key or not api_key or len(api_key) < 20:
        print("Invalid API key detected. Using fallback mode for image identification.")
        USE_FALLBACK_MODE = True
        return generate_fallback_identification(image_path)
    
    try:
        # Read image and convert to base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "gpt-4-vision-preview",  # Using latest GPT-4 Vision model
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Identify this species with scientific name and category. If you're unsure, indicate your confidence level. Focus on species found in Islamabad, Pakistan."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }
        
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response_data = response.json()
        
        if 'choices' in response_data:
            result = response_data['choices'][0]['message']['content']
            return {
                'success': True,
                'result': result,
                'species': extract_species_from_result(result)
            }
        else:
            print(f"API error response: {response_data}")
            USE_FALLBACK_MODE = True
            return generate_fallback_identification(image_path)
    
    except Exception as e:
        print(f"Error in image identification: {e}")
        traceback.print_exc()
        USE_FALLBACK_MODE = True
        return generate_fallback_identification(image_path)

def generate_fallback_identification(image_path):
    """Generate a fallback identification when API is not available"""
    # Extract filename as a basic way to guess the species
    filename = os.path.basename(image_path).lower()
    
    # Remove random prefix if there is one (like UUID_)
    if '_' in filename:
        parts = filename.split('_', 1)
        if len(parts) > 1:
            filename = parts[1]
    
    # Remove file extension
    filename = os.path.splitext(filename)[0]
    
    # List of common wildlife in Islamabad that we might detect
    common_wildlife = {
        'leopard': {
            'name': 'Common Leopard',
            'scientific': 'Panthera pardus',
            'category': 'Mammal'
        },
        'deer': {
            'name': 'Barking Deer',
            'scientific': 'Muntiacus muntjak',
            'category': 'Mammal'
        },
        'fox': {
            'name': 'Red Fox',
            'scientific': 'Vulpes vulpes',
            'category': 'Mammal'
        },
        'bird': {
            'name': 'Himalayan Griffon',
            'scientific': 'Gyps himalayensis',
            'category': 'Bird'
        },
        'eagle': {
            'name': 'Steppe Eagle',
            'scientific': 'Aquila nipalensis',
            'category': 'Bird'
        },
        'duck': {
            'name': 'Mallard Duck',
            'scientific': 'Anas platyrhynchos',
            'category': 'Bird'
        },
        'snake': {
            'name': 'Indian Cobra',
            'scientific': 'Naja naja',
            'category': 'Reptile'
        }
    }
    
    # Check if filename contains any of our known species
    for keyword, info in common_wildlife.items():
        if keyword in filename:
            return {
                'success': True,
                'result': f"This appears to be a {info['name']} ({info['scientific']}), which is a {info['category']} found in Islamabad, Pakistan. (Note: This is an offline identification)",
                'species': {
                    'name': info['name'],
                    'confidence': 0.7
                }
            }
    
    # Default fallback response
    return {
        'success': True,
        'result': "This appears to be a wildlife species from Islamabad, Pakistan. For accurate identification, please try again when the AI service is available. (Note: This is an offline identification)",
        'species': {
            'name': 'Unknown Wildlife Species',
            'confidence': 0.5
        }
    }

def extract_species_from_result(result_text):
    """Extract species name and confidence from GPT response"""
    # Simple extraction logic - would need enhancement for production
    if "identified as" in result_text.lower():
        species_part = result_text.lower().split("identified as")[1].strip()
        species_name = species_part.split(".")[0].strip()
        return {
            'name': species_name,
            'confidence': get_confidence_from_text(result_text)
        }
    return None

def get_confidence_from_text(text):
    """Extract confidence level from GPT response"""
    if "high confidence" in text.lower():
        return 0.9
    elif "medium confidence" in text.lower():
        return 0.7
    elif "low confidence" in text.lower():
        return 0.5
    return 0.6  # Default moderate confidence 
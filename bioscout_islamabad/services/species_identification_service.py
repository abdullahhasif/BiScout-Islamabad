"""
Species Identification Service

This module provides functions for identifying species from images 
using OpenAI's GPT-4 Vision API.
"""

import os
import requests
import base64
import logging
from config import Config

# Set up logging
logger = logging.getLogger(__name__)

def get_species_from_image(image_path):
    """
    Identify species in an image using GPT-4 Vision API
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        dict: A dictionary containing identification results with keys:
            - success (bool): Whether identification was successful
            - result (str): The full text response from GPT-4
            - species (dict, optional): Extracted species info with name and confidence
            - error (str, optional): Error message if identification failed
    """
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return {
            'success': False,
            'error': 'Image file not found'
        }
    
    if not Config.OPENAI_API_KEY:
        logger.error("OpenAI API key is missing")
        return {
            'success': False,
            'error': 'OpenAI API key not configured'
        }
    
    try:
        # Read image and convert to base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Config.OPENAI_API_KEY}"
        }
        
        payload = {
            "model": "gpt-4-vision-preview",
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
        
        response = requests.post("https://api.openai.com/v1/chat/completions", 
                               headers=headers, 
                               json=payload, 
                               timeout=30)
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return {
                'success': False,
                'error': f'API error: {response.status_code}',
                'details': response.text
            }
        
        response_data = response.json()
        
        if 'choices' in response_data:
            result = response_data['choices'][0]['message']['content']
            logger.info("Species identification successful")
            return {
                'success': True,
                'result': result,
                'species': extract_species_from_result(result)
            }
        else:
            logger.error(f"Unexpected API response format: {response_data}")
            return {
                'success': False,
                'error': 'Unexpected API response format',
                'details': response_data
            }
    
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        return {
            'success': False,
            'error': 'API request timed out'
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return {
            'success': False,
            'error': f'Request error: {str(e)}'
        }
    except Exception as e:
        logger.exception(f"Unexpected error during species identification: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def extract_species_from_result(result_text):
    """
    Extract species name and confidence from GPT response
    
    Args:
        result_text (str): The text response from GPT-4
        
    Returns:
        dict or None: Dictionary with species name and confidence, or None if extraction failed
    """
    if not result_text:
        return None
    
    try:
        result_lower = result_text.lower()
        
        # Try different patterns for extraction
        if "identified as" in result_lower:
            species_part = result_lower.split("identified as")[1].strip()
            species_name = species_part.split(".")[0].strip()
            return {
                'name': species_name.capitalize(),
                'confidence': get_confidence_from_text(result_text)
            }
        elif "species:" in result_lower:
            lines = result_lower.split("\n")
            for line in lines:
                if "species:" in line:
                    species_name = line.split("species:")[1].strip()
                    return {
                        'name': species_name.capitalize(),
                        'confidence': get_confidence_from_text(result_text)
                    }
        elif "this is a" in result_lower:
            species_part = result_lower.split("this is a")[1].strip()
            species_name = species_part.split(".")[0].strip()
            return {
                'name': species_name.capitalize(),
                'confidence': get_confidence_from_text(result_text)
            }
        
        # If no pattern matches, use first 50 chars as fallback
        return {
            'name': result_text[:50].strip(),
            'confidence': 0.5  # Medium confidence for fallback
        }
    except Exception as e:
        logger.error(f"Error extracting species from result: {e}")
        return None

def get_confidence_from_text(text):
    """
    Extract confidence level from GPT response
    
    Args:
        text (str): The text response from GPT-4
        
    Returns:
        float: Confidence level between 0.0 and 1.0
    """
    text_lower = text.lower()
    
    if "high confidence" in text_lower or "certain" in text_lower:
        return 0.9
    elif "medium confidence" in text_lower or "fairly certain" in text_lower:
        return 0.7
    elif "low confidence" in text_lower or "uncertain" in text_lower:
        return 0.4
    elif "very low confidence" in text_lower:
        return 0.2
    
    # Default moderate confidence
    return 0.6 
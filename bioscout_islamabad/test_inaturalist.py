#!/usr/bin/env python3
"""
Test script for iNaturalist API integration
This script tests the connection to the iNaturalist API and can identify a species from an image
"""

import os
import sys
import json
import argparse
import mimetypes
from dotenv import load_dotenv
import logging
from services.inaturalist_service import inaturalist_service

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_colored(text, color='default'):
    """Print colored text to the console"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'default': '\033[0m'
    }
    end_color = '\033[0m'
    
    color_code = colors.get(color, colors['default'])
    print(f"{color_code}{text}{end_color}")

def test_connection():
    """Test the connection to the iNaturalist API"""
    print_colored("Testing connection to iNaturalist API...", "blue")
    
    # Try to test the connection
    result = inaturalist_service.test_connection()
    
    if result['success']:
        print_colored(f"✅ Success: {result['message']}", "green")
        print_colored(f"Rate limit remaining: {result.get('rate_limit_remaining', 'Unknown')}", "green")
    else:
        print_colored(f"❌ Failed: {result['message']}", "red")
        print_colored("Please check your API token in the .env file.", "yellow")
        
    return result['success']

def is_valid_image(image_path):
    """Check if the path points to a valid image file"""
    if not os.path.exists(image_path):
        print_colored(f"❌ Error: Image file not found: {image_path}", "red")
        return False
    
    if not os.path.isfile(image_path):
        print_colored(f"❌ Error: {image_path} is not a file", "red")
        return False
        
    # Check if it's an image file by mime type
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type or not mime_type.startswith('image/'):
        print_colored(f"❌ Error: {image_path} does not appear to be an image file (mime type: {mime_type})", "red")
        print_colored("Please provide a valid image file (jpg, png, etc.)", "yellow")
        return False
        
    # Check file size
    file_size = os.path.getsize(image_path) / (1024 * 1024)  # Size in MB
    if file_size > 10:
        print_colored(f"⚠️ Warning: Image file is large ({file_size:.1f} MB). API may reject very large files.", "yellow")
        
    return True

def identify_image(image_path):
    """Identify a species from an image"""
    if not is_valid_image(image_path):
        return False
        
    print_colored(f"Identifying species in image: {image_path}", "blue")
    print_colored("This may take a few moments...", "blue")
    
    # Try to identify the species
    result = inaturalist_service.identify_species_from_upload(image_path)
    
    if result['success']:
        print_colored("✅ Species identification successful!", "green")
        print_colored(f"Identification: {result['identification_text']}", "green")
        
        # Print top result details
        top_result = result.get('top_result', {})
        if top_result:
            print_colored("\nTop Result Details:", "blue")
            print(f"Common name: {top_result.get('common_name', 'Unknown')}")
            print(f"Scientific name: {top_result.get('scientific_name', 'Unknown')}")
            print(f"Confidence: {top_result.get('confidence', 0)}%")
            print(f"Category: {top_result.get('category', 'Unknown')}")
            
            # Print taxonomy
            taxonomy = top_result.get('taxonomy', {})
            if taxonomy:
                print_colored("\nTaxonomy:", "blue")
                for key, value in taxonomy.items():
                    if value:
                        print(f"  {key.capitalize()}: {value}")
            
            # Print conservation status if available
            if "conservation_status" in top_result and top_result["conservation_status"]:
                status = top_result["conservation_status"]
                print_colored("\nConservation Status:", "blue")
                if "status" in status:
                    print(f"Status: {status['status']}")
                if "authority" in status:
                    print(f"Authority: {status['authority']}")
            
            # Print Wikipedia URL if available
            if top_result.get('wikipedia_url'):
                print_colored("\nMore Information:", "blue")
                print(f"Wikipedia: {top_result.get('wikipedia_url')}")
            
            # Print additional results
            other_results = result.get('results', [])[1:]
            if other_results:
                print_colored("\nOther Possibilities:", "blue")
                for i, other in enumerate(other_results, 1):
                    print(f"{i}. {other.get('common_name', 'Unknown')} ({other.get('scientific_name', 'Unknown')}) - {other.get('confidence', 0)}% confidence")
        
        print_colored("\nThis species identification can now be used in the BioScout application!", "green")
    else:
        print_colored(f"❌ Failed: {result.get('message', 'Unknown error')}", "red")
        print_colored("Troubleshooting tips:", "yellow")
        print_colored("1. Make sure the image is clear and shows the species well", "yellow")
        print_colored("2. Check that your API token is correct in the .env file", "yellow")
        print_colored("3. The API might be rate-limited or temporarily unavailable", "yellow")
    
    return result['success']

def main():
    """Main function to run the tests"""
    load_dotenv()  # Load environment variables from .env file
    
    parser = argparse.ArgumentParser(description="Test iNaturalist API integration")
    parser.add_argument("--image", "-i", help="Path to an image file to identify")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('services.inaturalist_service').setLevel(logging.DEBUG)
    
    # Show initial message
    print_colored("iNaturalist API Test Tool", "blue")
    print_colored("======================\n", "blue")
    
    # Check if API token is set
    if not inaturalist_service.api_token:
        print_colored("⚠️ Warning: No iNaturalist API token found in environment variables.", "yellow")
        print_colored("Anonymous requests have lower rate limits and may not work for all features.", "yellow")
        print_colored("Add your token to the .env file as INATURALIST_API_TOKEN=your_token_here\n", "yellow")
    
    # Always test the connection first
    connection_successful = test_connection()
    print()
    
    if args.image:
        # If an image was provided, try to identify it
        if connection_successful:
            identify_image(args.image)
        else:
            print_colored("Skipping image identification due to connection failure", "yellow")
    elif connection_successful:
        # If no image was provided but connection was successful, suggest using one
        print_colored("Connection test successful! To identify a species, run:", "blue")
        print_colored(f"  python {sys.argv[0]} --image <path_to_image>", "blue")
        print_colored("You can also try one of the sample images:", "blue")
        print_colored("  python {sys.argv[0]} --image static/images/samples/leopard.jpg", "blue")
    
if __name__ == "__main__":
    main() 
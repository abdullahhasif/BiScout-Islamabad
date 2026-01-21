import requests
import os
import sys
import json
from requests_toolbelt.multipart.encoder import MultipartEncoder

class iNaturalistSpeciesIdentifier:
    """
    Simple command-line tool to identify species using the iNaturalist API
    """
    
    def __init__(self):
        self.base_url = "https://api.inaturalist.org/v1"
    
    def identify_species(self, image_path):
        """
        Identify species in an image using iNaturalist's Computer Vision API
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            list: Possible species matches with confidence scores
        """
        print(f"Analyzing image: {image_path}")
        print("Sending to iNaturalist API...\n")
        
        with open(image_path, "rb") as image_file:
            multipart_data = MultipartEncoder(
                fields={
                    "image": (os.path.basename(image_path), image_file, "image/jpeg")
                }
            )
            
            headers = {
                "Content-Type": multipart_data.content_type
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/computervision",
                    data=multipart_data,
                    headers=headers
                )
                
                response.raise_for_status()  # Raise exception for HTTP errors
                
                return response.json().get("results", [])
                
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")
                if hasattr(e, 'response') and e.response:
                    print(f"Response status code: {e.response.status_code}")
                    print(f"Response text: {e.response.text}")
                return []

    def print_results(self, results, limit=5):
        """
        Print formatted results to the console
        
        Args:
            results (list): List of species matches
            limit (int): Maximum number of results to display
        """
        if not results:
            print("No species matches found. Try uploading a clearer image.")
            return
        
        print("=" * 60)
        print("TOP SPECIES MATCHES")
        print("=" * 60)
        
        for i, result in enumerate(results[:limit]):
            if i >= limit:
                break
                
            taxon = result["taxon"]
            score = result["score"] * 100
            
            common_name = taxon.get("preferred_common_name", "No common name")
            scientific_name = taxon["name"]
            
            print(f"{i+1}. {common_name} ({scientific_name})")
            print(f"   Confidence: {score:.2f}%")
            
            # Additional information if available
            if "iconic_taxon_name" in taxon:
                print(f"   Category: {taxon['iconic_taxon_name']}")
                
            if "wikipedia_url" in taxon:
                print(f"   Wikipedia: {taxon['wikipedia_url']}")
                
            print(f"   iNaturalist: https://www.inaturalist.org/taxa/{taxon['id']}")
            print("-" * 60)


def main():
    """
    Main function to run the species identifier
    """
    # Check if an image path was provided
    if len(sys.argv) < 2:
        print("Usage: python species_identifier.py <image_path>")
        print("Example: python species_identifier.py butterfly.jpg")
        return
    
    image_path = sys.argv[1]
    
    # Check if the file exists
    if not os.path.isfile(image_path):
        print(f"Error: File '{image_path}' does not exist")
        return
    
    # Check if the file is an image
    valid_extensions = ['.jpg', '.jpeg', '.png']
    if not any(image_path.lower().endswith(ext) for ext in valid_extensions):
        print(f"Error: File '{image_path}' is not a supported image format")
        print(f"Supported formats: {', '.join(valid_extensions)}")
        return
    
    # Create the identifier and process the image
    identifier = iNaturalistSpeciesIdentifier()
    results = identifier.identify_species(image_path)
    identifier.print_results(results)
    
    if results:
        top_match = results[0]["taxon"]
        print(f"\nBest match: {top_match.get('preferred_common_name', 'Unknown')} ({top_match['name']})")
        print(f"Confidence: {results[0]['score'] * 100:.2f}%")


if __name__ == "__main__":
    # Required packages: requests, requests_toolbelt
    # pip install requests requests_toolbelt
    main()
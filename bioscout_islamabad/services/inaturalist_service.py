"""
iNaturalist API Service - Provides integration with iNaturalist for species identification
"""

import os
import requests
import json
from typing import Dict, List, Optional, Union
from requests_toolbelt.multipart.encoder import MultipartEncoder
from datetime import datetime, timedelta
import logging
import time

from config import Config

# Set up logging
logger = logging.getLogger(__name__)

class INaturalistService:
    """
    Service for interacting with the iNaturalist API for species identification
    and observation management.
    
    API Documentation: https://api.inaturalist.org/v1/docs/
    """
    
    def __init__(self, api_token=None):
        """
        Initialize the iNaturalist client
        
        Args:
            api_token (str, optional): iNaturalist API token
        """
        self.base_url = Config.INATURALIST_API_BASE_URL
        self.api_token = api_token or Config.INATURALIST_API_TOKEN
        self.jwt_token = None
        self.jwt_expiry = None
        self.rate_limit_remaining = 100  # Default to 100 requests
        self.rate_limit_reset = None
        
    def get_jwt_token(self) -> str:
        """
        Get a JWT token using the API token
        JWT tokens expire after 24 hours, so this checks if the token is expired
        and gets a new one if needed.
        
        Returns:
            str: JWT token for authentication
        """
        if not self.api_token:
            raise ValueError("API token is required for authentication")
        
        # Check if token exists and is still valid (with 30 min buffer)
        current_time = datetime.now()
        if (self.jwt_token and self.jwt_expiry and 
            current_time < self.jwt_expiry - timedelta(minutes=30)):
            return self.jwt_token
            
        headers = {
            "Authorization": f"Bearer {self.api_token}"
        }
        
        try:
            logger.info("Requesting new JWT token from iNaturalist")
            response = requests.get(
                "https://www.inaturalist.org/users/api_token",
                headers=headers
            )
            
            response.raise_for_status()
            
            # Store the new token and set expiry time (24 hours from now)
            self.jwt_token = response.json().get("api_token")
            self.jwt_expiry = current_time + timedelta(hours=24)
            
            logger.info(f"Successfully obtained new JWT token, valid until {self.jwt_expiry}")
            return self.jwt_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting JWT token: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def _handle_rate_limits(self, response):
        """
        Handle rate limiting by checking headers and waiting if necessary
        
        Args:
            response (requests.Response): Response object from a request
        """
        # Check for rate limit headers
        if 'X-RateLimit-Remaining' in response.headers:
            self.rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
            
        if 'X-RateLimit-Reset' in response.headers:
            self.rate_limit_reset = int(response.headers['X-RateLimit-Reset'])
        
        # If we're close to hitting the rate limit, log a warning
        if self.rate_limit_remaining < 10:
            logger.warning(f"iNaturalist API rate limit almost reached: {self.rate_limit_remaining} requests remaining")
            
        # If we've hit the rate limit, wait until reset time
        if self.rate_limit_remaining <= 0 and self.rate_limit_reset:
            current_time = int(time.time())
            wait_time = max(0, self.rate_limit_reset - current_time)
            if wait_time > 0:
                logger.warning(f"Rate limit exceeded, waiting {wait_time} seconds before next request")
                time.sleep(wait_time)
    
    def identify_species(self, image_path: str) -> List[Dict]:
        """
        Identify species in an image using the iNaturalist Computer Vision API
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            list: Possible species matches with confidence scores
        """
        logger.info(f"Analyzing image: {image_path}")
        
        with open(image_path, "rb") as image_file:
            multipart_data = MultipartEncoder(
                fields={
                    "image": (os.path.basename(image_path), image_file, "image/jpeg")
                }
            )
            
            headers = {
                "Content-Type": multipart_data.content_type,
                "Accept": "application/json"
            }
            
            # Add authentication if available
            if self.api_token:
                try:
                    jwt = self.get_jwt_token()
                    headers["Authorization"] = jwt
                except Exception as e:
                    logger.warning(f"Failed to get JWT token, proceeding without authentication: {e}")
            
            try:
                # The correct endpoint is /v1/computer_vision not /v1/computervision
                response = requests.post(
                    f"{self.base_url}/computer_vision",
                    data=multipart_data,
                    headers=headers
                )
                
                # Handle rate limiting
                self._handle_rate_limits(response)
                
                response.raise_for_status()
                
                return response.json().get("results", [])
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error identifying species: {e}")
                if hasattr(e, 'response') and e.response:
                    logger.error(f"Response: {e.response.text}")
                    
                    # Handle specific error cases
                    if e.response.status_code == 429:
                        logger.warning("Rate limit exceeded. Consider reducing request frequency.")
                    elif e.response.status_code == 401:
                        logger.warning("Authentication failed. Check your API token.")
                    elif e.response.status_code == 404:
                        # Try alternative endpoint if the first one fails
                        logger.warning("Computer vision endpoint not found, trying alternative endpoint...")
                        try:
                            # Reset the file pointer
                            image_file.seek(0)
                            
                            # Try the /v1/vision endpoint as a fallback
                            alt_response = requests.post(
                                f"{self.base_url}/vision",
                                data=multipart_data,
                                headers=headers
                            )
                            alt_response.raise_for_status()
                            return alt_response.json().get("results", [])
                        except requests.exceptions.RequestException as alt_e:
                            logger.error(f"Alternative endpoint also failed: {alt_e}")
                        
                return []
    
    def get_taxon_details(self, taxon_id: Union[int, str]) -> Dict:
        """
        Get detailed information about a specific taxon using the Taxa API
        
        Args:
            taxon_id (int or str): The ID of the taxon to retrieve
            
        Returns:
            dict: Detailed taxon information or empty dict if not found
        """
        if not taxon_id:
            return {}
            
        headers = {"Accept": "application/json"}
        
        try:
            response = requests.get(
                f"{self.base_url}/taxa/{taxon_id}",
                headers=headers
            )
            
            # Handle rate limiting
            self._handle_rate_limits(response)
            
            response.raise_for_status()
            
            results = response.json().get("results", [])
            if results:
                return results[0]
            return {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting taxon details for ID {taxon_id}: {e}")
            return {}
    
    def format_identification_result(self, results: List[Dict], limit: int = None) -> Dict:
        """
        Format the identification results into a structured response
        
        Args:
            results (List[Dict]): The identification results from iNaturalist
            limit (int, optional): Maximum number of results to include. If None, uses the config setting.
            
        Returns:
            Dict: Formatted identification data
        """
        if limit is None:
            limit = Config.MAX_IDENTIFICATION_RESULTS
            
        if not results:
            return {
                "success": False,
                "message": "No species identified",
                "results": []
            }
        
        formatted_results = []
        
        for i, result in enumerate(results[:limit]):
            if i >= limit:
                break
                
            taxon = result["taxon"]
            score = result["score"] * 100
            
            common_name = taxon.get("preferred_common_name", "Unknown")
            scientific_name = taxon["name"]
            
            # Determine if it's a plant or animal
            kingdom = "Unknown"
            phylum = "Unknown"
            class_name = "Unknown"
            order = "Unknown"
            family = "Unknown"
            
            for ancestor in taxon.get("ancestors", []):
                rank = ancestor.get("rank")
                if rank == "kingdom":
                    kingdom = ancestor.get("name", "Unknown")
                elif rank == "phylum":
                    phylum = ancestor.get("name", "Unknown")
                elif rank == "class":
                    class_name = ancestor.get("name", "Unknown")
                elif rank == "order":
                    order = ancestor.get("name", "Unknown")
                elif rank == "family":
                    family = ancestor.get("name", "Unknown")
            
            is_plant = kingdom.lower() == "plantae"
            is_animal = kingdom.lower() == "animalia"
            
            category = "Other"
            if is_plant:
                category = "Plant"
            elif is_animal:
                category = "Animal"
            
            # Get more detailed information for the top result
            detailed_info = {}
            if i == 0:
                detailed_info = self.get_taxon_details(taxon["id"])
            
            # Build the formatted result
            formatted_result = {
                "taxon_id": taxon["id"],
                "common_name": common_name,
                "scientific_name": scientific_name,
                "confidence": round(score, 2),
                "category": category,
                "is_plant": is_plant,
                "is_animal": is_animal,
                "taxonomy": {
                    "kingdom": kingdom,
                    "phylum": phylum,
                    "class": class_name,
                    "order": order,
                    "family": family,
                    "genus": taxon.get("genus_name", ""),
                    "species": taxon.get("species_name", ""),
                    "rank": taxon.get("rank", "unknown"),
                },
                "wikipedia_url": taxon.get("wikipedia_url", ""),
                "default_photo": taxon.get("default_photo", {})
            }
            
            # Add additional fields from detailed info if available
            if detailed_info:
                if "conservation_status" in detailed_info:
                    formatted_result["conservation_status"] = detailed_info["conservation_status"]
                if "atlas_id" in detailed_info:
                    formatted_result["atlas_id"] = detailed_info["atlas_id"]
                if "wikipedia_summary" in detailed_info:
                    formatted_result["wikipedia_summary"] = detailed_info["wikipedia_summary"]
            
            formatted_results.append(formatted_result)
        
        top_result = formatted_results[0] if formatted_results else None
        
        # Build a descriptive identification text
        identification_text = ""
        if top_result:
            identification_text = f"This appears to be a {top_result['common_name']} ({top_result['scientific_name']})"
            
            if top_result['category'] == 'Plant':
                identification_text += f", a plant species in the {top_result['taxonomy']['family']} family"
            elif top_result['category'] == 'Animal':
                identification_text += f", an animal species in the {top_result['taxonomy']['family']} family"
            
            # Add conservation status if available
            if "conservation_status" in top_result and top_result["conservation_status"]:
                status = top_result["conservation_status"]
                if "status" in status:
                    identification_text += f". Conservation status: {status['status']}"
                    
            if top_result['wikipedia_url']:
                identification_text += f". More information can be found on Wikipedia."
        
        return {
            "success": True,
            "message": "Species identified successfully",
            "identification_text": identification_text,
            "top_result": top_result,
            "results": formatted_results
        }

    def identify_species_from_upload(self, uploaded_file_path: str) -> Dict:
        """
        Identify a species from an uploaded file
        
        Args:
            uploaded_file_path (str): Path to the uploaded image file
            
        Returns:
            Dict: Identification results with formatted response
        """
        try:
            # Check if the file exists
            if not os.path.exists(uploaded_file_path):
                return {
                    "success": False,
                    "message": f"File not found: {uploaded_file_path}"
                }
                
            # Try to identify the species
            results = self.identify_species(uploaded_file_path)
            
            # Format the results
            return self.format_identification_result(results)
            
        except Exception as e:
            logger.error(f"Error in species identification: {e}")
            return {
                "success": False,
                "message": f"Error identifying species: {str(e)}",
                "results": []
            }
    
    def test_connection(self) -> Dict:
        """
        Test the connection to the iNaturalist API
        
        Returns:
            Dict: Test result with success status and message
        """
        try:
            # Try to get a JWT token if API token is provided
            if self.api_token:
                self.get_jwt_token()
                
            # Test the API by making a simple request to the taxa endpoint
            response = requests.get(
                f"{self.base_url}/taxa?per_page=1",
                headers={"Accept": "application/json"}
            )
            
            self._handle_rate_limits(response)
            response.raise_for_status()
            
            return {
                "success": True,
                "message": "Connection to iNaturalist API successful",
                "rate_limit_remaining": self.rate_limit_remaining
            }
            
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            if hasattr(e, 'response') and e.response:
                try:
                    error_detail = e.response.json()
                    error_message = f"{error_message}: {error_detail}"
                except:
                    error_message = f"{error_message}: {e.response.text}"
                    
            return {
                "success": False,
                "message": f"Connection to iNaturalist API failed: {error_message}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error testing iNaturalist API connection: {str(e)}"
            }

# Create a singleton instance
inaturalist_service = INaturalistService() 
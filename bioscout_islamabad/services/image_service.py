"""
Image Service

This module handles image processing operations, particularly EXIF data extraction
for geolocation information from images.
"""

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

def get_exif_data(image_path):
    """
    Extract EXIF data from an image
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        dict: Dictionary containing EXIF data, including GPS information if available
    """
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return {}
    
    try:
        image = Image.open(image_path)
        exif_data = {}
        
        if hasattr(image, '_getexif') and image._getexif() is not None:
            exif = image._getexif()
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'GPSInfo':
                    gps_data = {}
                    for gps_tag_id in value:
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_data[gps_tag] = value[gps_tag_id]
                    exif_data[tag] = gps_data
                else:
                    exif_data[tag] = value
        
        return exif_data
    except (IOError, AttributeError) as e:
        logger.error(f"Error opening image or reading EXIF data: {e}")
        return {}
    except Exception as e:
        logger.exception(f"Unexpected error extracting EXIF data: {e}")
        return {}

def get_coordinates_from_exif(exif_data):
    """
    Extract GPS coordinates from EXIF data
    
    Args:
        exif_data (dict): Dictionary containing EXIF data
        
    Returns:
        list or None: List containing [longitude, latitude] or None if not found
    """
    if not exif_data or 'GPSInfo' not in exif_data:
        return None
    
    try:
        gps_info = exif_data['GPSInfo']
        
        # Extract latitude
        if 'GPSLatitude' in gps_info and 'GPSLatitudeRef' in gps_info:
            lat_data = gps_info['GPSLatitude']
            lat_ref = gps_info['GPSLatitudeRef']
            
            latitude = (lat_data[0] + lat_data[1]/60 + lat_data[2]/3600)
            if lat_ref == 'S':
                latitude = -latitude
        else:
            return None
        
        # Extract longitude
        if 'GPSLongitude' in gps_info and 'GPSLongitudeRef' in gps_info:
            lon_data = gps_info['GPSLongitude']
            lon_ref = gps_info['GPSLongitudeRef']
            
            longitude = (lon_data[0] + lon_data[1]/60 + lon_data[2]/3600)
            if lon_ref == 'W':
                longitude = -longitude
        else:
            return None
        
        # Return [longitude, latitude] for GeoJSON compatibility
        return [longitude, latitude]
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Error extracting coordinates from EXIF: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error processing coordinates: {e}")
        return None

def get_image_dimensions(image_path):
    """
    Get dimensions of an image
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        tuple or None: (width, height) or None if failed
    """
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return None
    
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception as e:
        logger.error(f"Error getting image dimensions: {e}")
        return None 
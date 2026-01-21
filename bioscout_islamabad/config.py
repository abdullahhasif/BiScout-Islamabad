import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration settings
    
    This class centralizes all configuration settings for the BioScout application.
    Environment variables are loaded from a .env file if present.
    
    Attributes:
        OPENAI_API_KEY (str): API key for OpenAI services
        UPLOAD_FOLDER (str): Path for uploaded images
        ALLOWED_EXTENSIONS (set): Allowed file extensions for uploads
        MAX_CONTENT_LENGTH (int): Maximum upload size in bytes
    """
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    INATURALIST_API_TOKEN = os.getenv('INATURALIST_API_TOKEN')
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    
    # Database settings
    DATABASE_DIR = 'data'
    
    # RAG system settings
    RAG_UPDATE_COOLDOWN = 60  # seconds
    
    # Map default center coordinates (Islamabad)
    DEFAULT_MAP_CENTER = [33.6844, 73.0479]
    DEFAULT_MAP_ZOOM = 12
    
    # Species classification settings
    ENABLE_AUTO_IDENTIFICATION = True  # Enable/disable auto-identification
    MAX_IDENTIFICATION_RESULTS = 3  # Maximum number of identification results to return
    
    # iNaturalist API settings
    INATURALIST_API_BASE_URL = "https://api.inaturalist.org/v1" 
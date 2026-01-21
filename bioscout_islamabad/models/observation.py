from datetime import datetime
from services import data_persistence_service as db_service

class Observation:
    def __init__(self, user_id, species_name=None, date_observed=None, location=None, 
                 coordinates=None, image_url=None, notes=None, ai_identification=None, 
                 category=None, quantity=None, habitat_type=None, species_type=None):
        self.user_id = user_id
        self.species_name = species_name
        self.date_observed = date_observed or datetime.now().isoformat()
        self.location = location
        self.coordinates = coordinates  # [longitude, latitude]
        self.image_url = image_url
        self.notes = notes
        self.ai_identification = ai_identification
        self.created_at = datetime.now().isoformat()
        self.category = category or self._determine_category()
        self.quantity = quantity or 1
        self.habitat_type = habitat_type
        self.species_type = species_type or self._determine_species_type()
    
    def _determine_category(self):
        """Determine if this is a plant or animal based on species name."""
        if not self.species_name:
            return 'unknown'
        
        return 'plant' if db_service.is_plant_species(self.species_name) else 'animal'
    
    def _determine_species_type(self):
        """Determine more specific type based on species name."""
        if not self.species_name:
            return None
            
        species_name = self.species_name.lower()
        
        if any(x in species_name for x in ['deer', 'leopard', 'fox', 'bear', 'boar']):
            return 'mammal'
        elif any(x in species_name for x in ['bird', 'duck', 'griffon', 'owl']):
            return 'bird'
        elif any(x in species_name for x in ['snake', 'cobra', 'lizard']):
            return 'reptile'
        elif any(x in species_name for x in ['frog', 'toad']):
            return 'amphibian'
        elif any(x in species_name for x in ['fish', 'carp']):
            return 'fish'
        elif any(x in species_name for x in ['pine', 'cedar', 'oak', 'palm']):
            return 'tree'
        elif db_service.is_plant_species(species_name):
            return 'plant'
            
        return None
    
    def save(self):
        """Save observation to CSV and return ID."""
        observation_data = {
            'user_id': self.user_id,
            'species_name': self.species_name,
            'date_observed': self.date_observed,
            'location': self.location,
            'coordinates': self.coordinates,
            'image_url': self.image_url,
            'notes': self.notes,
            'ai_identification': self.ai_identification,
            'created_at': self.created_at,
            'category': self.category,
            'quantity': self.quantity,
            'habitat_type': self.habitat_type,
            'species_type': self.species_type
        }
        return db_service.save_observation(observation_data)
    
    @staticmethod
    def find_by_id(observation_id):
        """Find observation by ID in CSV."""
        return db_service.find_observation_by_id(observation_id)
    
    @staticmethod
    def find_all():
        """Find all observations in CSV."""
        return db_service.find_all_observations()
    
    @staticmethod
    def find_plants():
        """Find all plant observations."""
        return db_service.find_all_plant_observations()
    
    @staticmethod
    def find_animals():
        """Find all animal observations."""
        return db_service.find_all_animal_observations()
    
    @staticmethod
    def find_by_species(species_name):
        """Find observations by species in CSV."""
        return db_service.find_observations_by_species(species_name)
    
    @staticmethod
    def find_by_location(location_name):
        """Find observations by location in CSV."""
        return db_service.find_observations_by_location(location_name)
    
    @staticmethod
    def find_by_category(category):
        """Find observations by category (plant or animal)."""
        return db_service.find_observations_by_category(category) 
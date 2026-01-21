from datetime import datetime
from services import data_persistence_service as db_service

class User:
    def __init__(self, username, email=None, full_name=None):
        self.username = username
        self.email = email
        self.full_name = full_name
        self.created_at = datetime.now().isoformat()
    
    def save(self):
        """Save user to CSV and return ID."""
        user_data = {
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'created_at': self.created_at
        }
        return db_service.save_user(user_data)
    
    @staticmethod
    def find_by_username(username):
        """Find user by username in CSV."""
        return db_service.find_user_by_username(username)
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID in CSV."""
        return db_service.find_user_by_id(user_id) 
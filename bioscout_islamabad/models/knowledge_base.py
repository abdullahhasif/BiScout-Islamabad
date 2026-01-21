from datetime import datetime
from services import data_persistence_service as db_service

class KnowledgeDocument:
    def __init__(self, title, content, source, category, region):
        self.title = title
        self.content = content
        self.source = source
        self.category = category
        self.region = region
        self.created_at = datetime.now().isoformat()
    
    def save(self):
        """Save knowledge document to CSV and return ID."""
        document_data = {
            'title': self.title,
            'content': self.content,
            'source': self.source,
            'category': self.category,
            'region': self.region,
            'created_at': self.created_at
        }
        return db_service.save_knowledge_document(document_data)
    
    @staticmethod
    def find_by_id(document_id):
        """Find knowledge document by ID in CSV."""
        return db_service.find_knowledge_document_by_id(document_id)
    
    @staticmethod
    def search(query):
        """Search knowledge documents in CSV."""
        return db_service.search_knowledge_documents(query) 
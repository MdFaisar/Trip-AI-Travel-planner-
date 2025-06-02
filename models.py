from datetime import datetime
from firebase_config import firebase_config
import uuid

class BaseModel:
    """Base model class with common methods"""
    
    def __init__(self, collection_name):
        self.db = firebase_config.get_db()
        self.collection_name = collection_name
        self.collection = self.db.collection(collection_name)
    
    def create(self, data):
        """Create a new document"""
        try:
            doc_ref = self.collection.add(data)
            return doc_ref[1].id
        except Exception as e:
            raise Exception(f"Error creating document: {e}")
    
    def get_by_id(self, doc_id):
        """Get document by ID"""
        try:
            doc = self.collection.document(doc_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            raise Exception(f"Error getting document: {e}")
    
    def update(self, doc_id, data):
        """Update document by ID"""
        try:
            self.collection.document(doc_id).update(data)
            return True
        except Exception as e:
            raise Exception(f"Error updating document: {e}")
    
    def delete(self, doc_id):
        """Delete document by ID"""
        try:
            self.collection.document(doc_id).delete()
            return True
        except Exception as e:
            raise Exception(f"Error deleting document: {e}")

class User(BaseModel):
    """User model"""
    
    def __init__(self):
        super().__init__('users')
    
    def create_user(self, uid, email, name, profile_picture=''):
        """Create a new user"""
        user_data = {
            'uid': uid,
            'email': email,
            'name': name,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'profile_picture': profile_picture,
            'preferences': {
                'currency': 'INR',
                'language': 'en',
                'notifications': True
            }
        }
        
        try:
            self.collection.document(uid).set(user_data)
            return user_data
        except Exception as e:
            raise Exception(f"Error creating user: {e}")
    
    def get_user_by_uid(self, uid):
        """Get user by UID"""
        try:
            doc = self.collection.document(uid).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            raise Exception(f"Error getting user: {e}")
    
    def get_user_by_email(self, email):
        """Get user by email"""
        try:
            users = self.collection.where('email', '==', email).limit(1).stream()
            for user in users:
                return user.to_dict()
            return None
        except Exception as e:
            raise Exception(f"Error getting user by email: {e}")
    
    def update_user(self, uid, data):
        """Update user data"""
        try:
            data['updated_at'] = datetime.now()
            self.collection.document(uid).update(data)
            return True
        except Exception as e:
            raise Exception(f"Error updating user: {e}")
    
    def update_profile_picture(self, uid, picture_url):
        """Update user profile picture"""
        return self.update_user(uid, {'profile_picture': picture_url})
    
    def update_preferences(self, uid, preferences):
        """Update user preferences"""
        return self.update_user(uid, {'preferences': preferences})

class Trip(BaseModel):
    """Trip model"""
    
    def __init__(self):
        super().__init__('trips')
    
    def create_trip(self, user_id, title, start_location, destination, 
                   start_date, end_date, budget, trip_plan=''):
        """Create a new trip"""
        trip_id = str(uuid.uuid4())
        duration = (end_date - start_date).days + 1
        
        trip_data = {
            'trip_id': trip_id,
            'user_id': user_id,
            'title': title,
            'start_location': start_location,
            'destination': destination,
            'start_date': start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date),
            'end_date': end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date),
            'duration': duration,
            'budget': budget,
            'trip_plan': trip_plan,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'status': 'draft',  # draft, completed, cancelled
            'is_favorite': False,
            'tags': [],
            'notes': ''
        }
        
        try:
            self.collection.document(trip_id).set(trip_data)
            return trip_data
        except Exception as e:
            raise Exception(f"Error creating trip: {e}")
    
    def get_trip_by_id(self, trip_id):
        """Get trip by ID"""
        try:
            doc = self.collection.document(trip_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            raise Exception(f"Error getting trip: {e}")
    
    def get_user_trips(self, user_id, limit=50, status=None):
        """Get all trips for a user"""
        try:
            query = self.collection.where('user_id', '==', user_id)
            
            if status:
                query = query.where('status', '==', status)
            
            query = query.order_by('created_at', direction='DESCENDING').limit(limit)
            
            trips = []
            for trip in query.stream():
                trips.append(trip.to_dict())
            
            return trips
        except Exception as e:
            raise Exception(f"Error getting user trips: {e}")
    
    def update_trip(self, trip_id, data):
        """Update trip data"""
        try:
            data['updated_at'] = datetime.now()
            self.collection.document(trip_id).update(data)
            return True
        except Exception as e:
            raise Exception(f"Error updating trip: {e}")
    
    def update_trip_plan(self, trip_id, trip_plan):
        """Update trip plan"""
        return self.update_trip(trip_id, {
            'trip_plan': trip_plan,
            'status': 'completed'
        })
    
    def mark_favorite(self, trip_id, is_favorite=True):
        """Mark trip as favorite"""
        return self.update_trip(trip_id, {'is_favorite': is_favorite})
    
    def add_notes(self, trip_id, notes):
        """Add notes to trip"""
        return self.update_trip(trip_id, {'notes': notes})
    
    def add_tags(self, trip_id, tags):
        """Add tags to trip"""
        return self.update_trip(trip_id, {'tags': tags})
    
    def delete_trip(self, trip_id):
        """Delete trip"""
        return self.delete(trip_id)
    
    def get_trip_statistics(self, user_id):
        """Get trip statistics for user"""
        try:
            trips = self.get_user_trips(user_id)
            
            stats = {
                'total_trips': len(trips),
                'completed_trips': len([t for t in trips if t.get('status') == 'completed']),
                'draft_trips': len([t for t in trips if t.get('status') == 'draft']),
                'favorite_trips': len([t for t in trips if t.get('is_favorite', False)]),
                'total_days': sum([t.get('duration', 0) for t in trips]),
                'countries_visited': len(set([t.get('destination', '').split(',')[0].strip() for t in trips if t.get('destination')])),
                'average_budget': sum([t.get('budget', {}).get('amount', 0) for t in trips]) / len(trips) if trips else 0
            }
            
            return stats
        except Exception as e:
            raise Exception(f"Error getting trip statistics: {e}")

# Model instances
user_model = User()
trip_model = Trip()
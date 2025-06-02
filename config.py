import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
    FIREBASE_WEB_API_KEY = os.getenv('FIREBASE_WEB_API_KEY')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    
    # Firebase configuration
    FIREBASE_CONFIG = {
        'apiKey': FIREBASE_WEB_API_KEY,
        'authDomain': f'{FIREBASE_PROJECT_ID}.firebaseapp.com',
        'projectId': FIREBASE_PROJECT_ID,
        'storageBucket': f'{FIREBASE_PROJECT_ID}.appspot.com',
        'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
        'appId': os.getenv('FIREBASE_APP_ID')
    }
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    
    # PDF settings
    PDF_TEMP_FOLDER = 'temp_pdfs'
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
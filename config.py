import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '1234')
    MYSQL_DB = os.getenv('MYSQL_DB', 'hospital_management_db')
    MYSQL_CURSORCLASS = 'DictCursor'
    
    # App Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here-2024')
    SESSION_PERMANENT = False
    SESSION_TYPE = 'filesystem'
    
    # Upload Configuration
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Pagination
    ITEMS_PER_PAGE = 10
    
    # Hospital Settings
    HOSPITAL_NAME = "City General Hospital"
    HOSPITAL_ADDRESS = "123 Healthcare Avenue, Medical District, City - 400001"
    HOSPITAL_PHONE = "+91 1234567890"
    HOSPITAL_EMAIL = "contact@cityhospital.com"
    GST_RATE = 0.18  # 18% GST

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
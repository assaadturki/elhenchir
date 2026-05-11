import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/farm_management'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_PERMANENT = False
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Upload settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Export settings
    EXPORT_FOLDER = 'exports'
    
    # Currency (Tunisian Dinar)
    CURRENCY = 'TND'
    CURRENCY_SYMBOL = 'د.ت'
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Date format
    DATE_FORMAT = '%d/%m/%Y'

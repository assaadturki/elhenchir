import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-CHANGE-IN-PRODUCTION'

    # Gestion automatique de la DB selon l'environnement
    _db_url = os.environ.get('DATABASE_URL', '')

    # Render fournit des URLs postgres:// → convertir en postgresql://
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

    # Fallback SQLite si rien de configuré
    if not _db_url:
        _base_dir = os.path.abspath(os.path.dirname(__file__))
        _db_url = 'sqlite:///' + os.path.join(_base_dir, 'farm_management.db')

    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    EXPORT_FOLDER = os.path.join(BASE_DIR, 'exports')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    CURRENCY = 'TND'
    CURRENCY_SYMBOL = 'د.ت'
    ITEMS_PER_PAGE = 20
    DATE_FORMAT = '%d/%m/%Y'

    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@farm.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    ADMIN_NOM = os.environ.get('ADMIN_NOM', 'Administrateur')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class ExeConfig(Config):
    DEBUG = False
    _base = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_base, 'farm_management.db')


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'exe': ExeConfig,
}

def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)

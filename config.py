import os

class Config:
    """
    Base configuration class.
    """
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_default_secret_key')
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///:memory:')

class DevelopmentConfig(Config):
    """
    Development configuration class.
    """
    DEBUG = True

class TestingConfig(Config):
    """
    Testing configuration class.
    """
    TESTING = True

class ProductionConfig(Config):
    """
    Production configuration class.
    """
    DATABASE_URL = os.environ.get('DATABASE_URL')

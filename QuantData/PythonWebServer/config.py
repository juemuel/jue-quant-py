# config.py
class Config:
    ENV = 'development'
    DEBUG = False
    TESTING = False
    SECRET_KEY = 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mydatabase.db'

class DevelopmentConfig(Config):
    ENV = 'development'
    DEBUG = True

class TestingConfig(Config):
    ENV = 'test'
    TESTING = True

class ProductionConfig(Config):
    ENV = 'production'
    pass
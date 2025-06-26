class Config:
    ENV = 'development'
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    ENV = 'development'
    DEBUG = True

class TestingConfig(Config):
    ENV = 'test'
    TESTING = True

class ProductionConfig(Config):
    ENV = 'production'

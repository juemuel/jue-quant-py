from flask import Flask
from config import Config, DevelopmentConfig, TestingConfig, ProductionConfig
from routes import bp

def create_app(config_name):
    app = Flask(__name__)

    # 根据传入的配置名称加载相应的配置
    if config_name == 'development':
        app.config.from_object(DevelopmentConfig)
    elif config_name == 'testing':
        app.config.from_object(TestingConfig)
    elif config_name == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(Config)

    # 注册蓝图
    app.register_blueprint(bp)

    return app
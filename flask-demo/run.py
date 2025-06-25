# run.py
from app import create_app

if __name__ == '__main__':
    # 根据需要选择配置
    config_name = 'development'  # 可以改为 'testing' 或 'production'
    app = create_app(config_name)
    app.run()
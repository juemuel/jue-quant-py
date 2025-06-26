import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件日志（带轮转）
    file_handler = RotatingFileHandler("app.log", maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

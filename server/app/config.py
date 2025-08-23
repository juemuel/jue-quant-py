# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    DATA_PROVIDER = os.getenv("DATA_PROVIDER", "akshare")
    
    # 新增调试模式配置
    DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
    DEBUG_DATA_PROVIDER = os.getenv("DEBUG_DATA_PROVIDER", "False").lower() == "true"
    DEBUG_STRATEGY = os.getenv("DEBUG_STRATEGY", "False").lower() == "true"
    DEBUG_BACKTEST = os.getenv("DEBUG_BACKTEST", "False").lower() == "true"
    DEBUG_SIGNALS = os.getenv("DEBUG_SIGNALS", "False").lower() == "true"
    
    # 调试输出级别
    DEBUG_LEVEL = os.getenv("DEBUG_LEVEL", "INFO").upper()  # DEBUG, INFO, WARNING, ERROR
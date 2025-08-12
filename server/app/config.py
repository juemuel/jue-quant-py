# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    DATA_PROVIDER = os.getenv("DATA_PROVIDER", "akshare")

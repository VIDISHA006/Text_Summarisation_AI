import os
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

# Load .env from parent folder of backend
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

def get_conn():
    """Return a MySQL connection using credentials in .env"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "ts_user"),
            password=os.getenv("DB_PASSWORD", "ts_password_123"),
            database=os.getenv("DB_NAME", "text_summarisation"),
        )
        return conn
    except Error as e:
        raise

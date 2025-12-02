import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import Config

#DATABASE CONNECTION
def get_db_connection():
    try:
        conn = psycopg2.connect(**Config.DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

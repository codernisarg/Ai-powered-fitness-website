import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",  # Direct value instead of using getenv
            user="root",
            password="root@123",
            database="gymDB"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return None

def create_tables():
    conn = get_db_connection()
    if conn is None:
        return False
    
    cursor = conn.cursor()
    try:
        # Create users table with session data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                session_id VARCHAR(255),
                session_expiry DATETIME
            )
        """)
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

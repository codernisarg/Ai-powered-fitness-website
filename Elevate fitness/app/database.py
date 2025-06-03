import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Function to establish a connection to the database
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("localhost"),
            user=os.getenv("root"),
            password=os.getenv("root@123"),
            database=os.getenv("gymDB"),
            port=os.getenv("3306", 3306)  # Default MySQL port
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

from flask import Flask
from app.utils.database import get_db
import mysql.connector
from werkzeug.security import check_password_hash

def create_user_table():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL,
        password VARCHAR(255) NOT NULL
    );
    ''')
    db.commit()
    cursor.close()

def get_user_by_email(email):
    db = mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your actual username
        password="root@123",  # Replace with your actual password
        database="gymDB"  # Replace with your actual database name
    )
    cursor = db.cursor(dictionary=True)  # Using dictionary to easily access columns by name
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    return user


def register_user(username, email, password):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
    INSERT INTO users (username, email, password)
    VALUES (%s, %s, %s);
    ''', (username, email, password))
    db.commit()
    cursor.close()

from werkzeug.security import check_password_hash

def authenticate_user(email, password):
    user = get_user_by_email(email)  # Ensure you get the user data from the DB correctly

    if user:
        hashed_password = user['password']  # Assuming user is a dict-like object with 'password'
        if check_password_hash(hashed_password, password):
            return user  # User authenticated successfully
        else:
            return None  # Password is incorrect
    return None  # User not found


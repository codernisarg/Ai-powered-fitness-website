from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.database import get_db_connection
import mysql.connector

user_routes = Blueprint("user_routes", __name__)

# Test Route
@user_routes.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "Blueprint is working!"}), 200

# User Signup
@user_routes.route("/signup", methods=["POST"])
def signup():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not all([name, email, password]):
        return jsonify({"error": "Missing required fields"}), 400

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password),
        )
        conn.commit()
        return jsonify({"message": "User registered successfully!"}), 201
    except mysql.connector.Error as e:
        conn.rollback()
        if e.errno == 1062:  # MySQL duplicate entry error
            return jsonify({"error": "Email already registered"}), 400
        return jsonify({"error": "Database error: " + str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# User Signin
@user_routes.route("/signin", methods=["POST"])
def signin():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            session.permanent = True
            return jsonify({"message": "Login successful"})
        
        return jsonify({"error": "Invalid credentials"}), 401

    finally:
        cursor.close()
        conn.close()

# User Logout
@user_routes.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

# Fetch User Profile (Protected Route)
@user_routes.route("/profile", methods=["GET"])
def get_profile():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized access"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT username, email, age, weight, height, fitness_goal FROM users WHERE id = %s", (session["user_id"],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user), 200

# Update User Profile (Protected Route)
@user_routes.route("/update-profile", methods=["POST"])
def update_profile():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized access"}), 401

    data = request.json
    age = data.get("age")
    weight = data.get("weight")
    height = data.get("height")
    fitness_goal = data.get("fitness_goal")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET age = %s, weight = %s, height = %s, fitness_goal = %s WHERE id = %s",
            (age, weight, height, fitness_goal, session["user_id"]),
        )
        conn.commit()
        return jsonify({"message": "Profile updated successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": "Database error: " + str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Restrict Access to Protected Pages
@user_routes.route("/protected", methods=["GET"])
def protected_route():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized access"}), 401
    return jsonify({"message": "Access granted", "user": session["username"]}), 200

@user_routes.route('/profile')
def profile():
    return render_template('profile.html')

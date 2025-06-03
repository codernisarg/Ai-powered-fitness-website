from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from app.routes.user_routes import user_routes
from app.routes.physique_routes import physique_routes
import google.generativeai as genai
import os
from dotenv import load_dotenv
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.database import get_db_connection
from datetime import timedelta

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

# Add a Secret Key for Session Management
app.secret_key = os.getenv("SECRET_KEY", "your_default_secret_key")
app.permanent_session_lifetime = timedelta(days=7)  # Set session lifetime

@app.before_request
def before_request():
    # Check if user is logged in
    if 'user_id' not in session and request.endpoint not in ['signin', 'signup', 'home', 'about', 'static']:
        return redirect(url_for('signin'))

# Register blueprints
app.register_blueprint(user_routes, url_prefix="/api")
app.register_blueprint(physique_routes, url_prefix="/physique")

# Set up Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("ERROR: GEMINI_API_KEY is not set! Check your .env file.")
genai.configure(api_key=GEMINI_API_KEY)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('signin', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        if not all([name, email, password]):
            return render_template('signup.html', error="All fields are required")
        conn = get_db_connection()
        if not conn:
            return render_template('signup.html', error="Database connection failed")
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return render_template('signup.html', error="Email already registered")
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (name, email, hashed_password)
            )
            conn.commit()
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            session['user_id'] = user['id']
            session['email'] = email
            session.permanent = True
            return redirect(url_for('home'))
        except Exception as e:
            print(f"Error during signup: {e}")
            return render_template('signup.html', error="Registration failed")
        finally:
            cursor.close()
            conn.close()
    return render_template('signup.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/bmi')
@login_required
def bmi():
    return render_template('bmi.html')

@app.route('/chatbot')
@login_required
def chatbot():
    return render_template('chatbot.html')

@app.route('/profile')
@login_required
def profile():
    conn = get_db_connection()
    if not conn:
        return render_template('profile.html', error="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT username, email, age, weight, height, fitness_goal 
            FROM users WHERE id = %s
            """,
            (session['user_id'],)
        )
        user_data = cursor.fetchone()
        if user_data is None:
            return render_template('profile.html', error="User not found")
        return render_template('profile.html', user=user_data)
    except Exception as e:
        print(f"Database error: {e}")
        return render_template('profile.html', error="Error fetching profile data")
    finally:
        cursor.close()
        conn.close()

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    if not request.is_json:
        return jsonify({"error": "Invalid request format"}), 400
    data = request.get_json()
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET age = %s, height = %s, weight = %s, fitness_goal = %s 
            WHERE id = %s
        """, (
            data.get('age'),
            data.get('height'),
            data.get('weight'),
            data.get('fitness_goal'),
            session['user_id']
        ))
        conn.commit()
        return jsonify({"message": "Profile updated successfully"}), 200
    except Exception as e:
        print(f"Error updating profile: {e}")
        return jsonify({"error": "Failed to update profile"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = get_db_connection()
        if not conn:
            return render_template('signin.html', error="Database connection failed")
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if user and check_password_hash(user['password'], password):
                session.permanent = True
                session['user_id'] = user['id']
                session['email'] = user['email']
                session['username'] = user['username']
                next_page = request.args.get('next')
                return redirect(next_page if next_page else url_for('home'))
            else:
                return render_template('signin.html', error="Invalid credentials")
        finally:
            cursor.close()
            conn.close()
    return render_template('signin.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/physique', methods=['GET', 'POST'])
@login_required
def physique():
    if request.method == 'POST':
        # Handle the form submission here
        pass
    return render_template('physique.html')

@app.route('/api/chatbot', methods=['POST'])
def chatbot_response():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"response": "Please enter a message."}), 400

    try:
        # Use gemini-1.5-flash model
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        prompt = f"""
        You are a friendly and expert fitness assistant. Your goal is to provide engaging, 
        helpful, and to-the-point advice about health, fitness, workouts, and nutrition.

        User: {user_message}
        Assistant:
        """
        
        response = model.generate_content(prompt)
        
        if response.text:
            return jsonify({"response": response.text}), 200
        else:
            return jsonify({"error": "No response generated"}), 500
            
    except Exception as e:
        print("Error with Gemini API:", e)
        return jsonify({"error": "Failed to generate response. Please try again."}), 500

# Example: Updated Physique Plan Generation endpoint
@app.route('/api/physique', methods=['POST'])
@login_required
def generate_physique_plan():
    if not request.is_json:
        return jsonify({"error": "Invalid request format"}), 400
        
    data = request.get_json()
    
    try:
        # Use gemini-1.5-flash model
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        prompt = f"""
        Create a concise, effective 4-week fitness plan considering:
        - Weight: {data['weight']} kg
        - Height: {data['height']} cm
        - Age: {data['age']}
        - Gender: {data['gender']}
        - Medical Conditions: {data.get('diseases', 'None')}

        Format the response as:
        1. Weekly Goals (max 2 lines)
        2. Workout Schedule (3-4 exercises per day, 4 days/week)
        3. Key Nutrition Tips (3-4 points)
        
        Keep it brief but effective.
        """
        
        response = model.generate_content(prompt)
        
        if response.text:
            return jsonify({"plan": response.text}), 200
        else:
            return jsonify({"error": "No response generated"}), 500
        
    except Exception as e:
        print(f"Error generating plan: {e}")
        return jsonify({"error": f"Failed to generate plan: {str(e)}"}), 500

def check_user_credentials(email, password):
    dummy_user = {"email": "user@example.com", "password": "password", "id": 1}
    if email == dummy_user['email'] and password == dummy_user['password']:
        return dummy_user
    return None

def list_available_models():
    """List all available models from Google Generative AI"""
    try:
        models = genai.list_models()
        available_models = [model.name for model in models]
        return available_models
    except Exception as e:
        print(f"Error listing models: {e}")
        return []

if __name__ == '__main__':
    app.run(debug=True)

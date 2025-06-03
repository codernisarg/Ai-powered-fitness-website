from flask import Blueprint, request, jsonify, render_template
from app.utils.database import get_db_connection
import google.generativeai as genai
import os
from dotenv import load_dotenv  # Load environment variables

physique_routes = Blueprint("physique_routes", __name__)

# Load environment variables from .env
load_dotenv()

# Retrieve the API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("⚠️ Warning: GEMINI_API_KEY is not set!")

@physique_routes.route("/")
def physique():
    return render_template('physique.html')

@physique_routes.route("/physique", methods=["POST"])
def generate_physique():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request, JSON expected"}), 400

    weight = data.get("weight")
    height = data.get("height")
    age = data.get("age")
    gender = data.get("gender")
    diseases = data.get("diseases", "")

    if not all([weight, height, age, gender]):
        return jsonify({"error": "Missing required fields"}), 400

    ai_prompt = f"""
    Create a SHORT & well-structured fitness plan for a {age}-year-old {gender} 
    with height {height} cm, weight {weight} kg, and diseases: {diseases}.

    **FORMAT:**
    Diet Plan:
    - Breakfast: (1-2 items)
    - Lunch: (1-2 items)
    - Dinner: (1-2 items)
    - Snacks: (1-2 items)

    Exercise Plan:
    - Cardio: (Duration & type)
    - Strength: (Exercise names)
    - Flexibility: (Exercise names)

    Keep it concise and easy to follow.
    """

    try:
        model = genai.GenerativeModel("gemini-pro")
        
        response = model.generate_content(
            ai_prompt,
            generation_config={
                "temperature": 0.0,
                "max_output_tokens": 300
            }
        )

        plan = response.text.strip() if response and response.text else "Error: No response from AI"

        return jsonify({"message": "Plan generated successfully!", "plan": plan}), 201

    except Exception as e:
        return jsonify({"error": f"Gemini AI error: {str(e)}"}), 500

from flask import Flask, request, jsonify, render_template
import os
import google.generativeai as genai
import json

app = Flask(__name__, template_folder=".")

# Konfiguracija
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# MODEL
MODEL_NAME = "gemini-2.5-pro"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        company_name = data.get('companyName')

        competitor_name = data.get('competitorName')
        # NOVO: Čitamo URL ako postoji
        competitor_url = data.get('competitorUrl', '')

        if not company_name or not competitor_name:
            return jsonify({"error": "Missing company names"}), 400

        # Model setup
        model = genai.GenerativeModel(MODEL_NAME)


        # PAMETNI PROMPT SA URL-om
        prompt = f"""
        Act as a ruthless expert business strategist.
        
        Compare these two companies:
        1. MY COMPANY: "{company_name}"
        2. COMPETITOR: "{competitor_name}"
        {f'3. COMPETITOR WEBSITE: "{competitor_url}" (Use this to identify their exact industry)' if competitor_url else ''}

        TASK:
        Analyze the strategic battle. If you don't know the specific companies, infer their business model based on their names/website and assume they operate in the same industry.
        
        Output valid JSON only:
        {{
            "score": number (0-100, higher is better for My Company),
            "winner": "string",
            "summary": "string (2 sentences executive summary)",
            "strengths": ["string", "string", "string"] (3 advantages of My Company),
            "weaknesses": ["string", "string", "string"] (3 vulnerabilities of Competitor),
            "verdict": "string (Brutally honest advice)"
        }}
        """

        response = model.generate_content(prompt)
        
        # Čišćenje JSON-a (za svaki slučaj)
        text_response = response.text.replace('```json', '').replace('```', '').strip()
        
        return jsonify(json.loads(text_response))

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "Analysis failed"}), 500

# Ovo je potrebno za Vercel
if __name__ == '__main__':

    app.run(debug=True)

import os
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- 1. KONFIGURACIJA ---
# ZAMENI SVOJ KLJUČ OVDE (PAZI NA NAVODNIKE!):
GEMINI_API_KEY = "AIzaSyB_Lz-oWQewsLyLKCUa5zAChGpqGeDpyX8" 

# Inicijalizacija AI modela
try:
    if not GEMINI_API_KEY or GEMINI_API_KEY == "OVDE_IDE_TVOJ_GEMINI_KLJUČ":
        print("UPOZORENJE: API ključ nije unet. AI neće raditi dok se ne unese.")
    else:
        genai.configure(api_key=GEMINI_API_KEY)

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config={"response_mime_type": "application/json"},
        safety_settings=[
            {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_NONE},

            {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_NONE},
            {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_NONE},
            {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_NONE},
        ]
    )
except Exception as e:
    print(f"FATALNA GREŠKA PRI INICIJALIZACIJI: {e}")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 2. SERVIRANJE SAJTA ---
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "index.html")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:

        return "<h1>Error: index.html not found</h1>"

# --- 3. GLAVNA LOGIKA (Univerzalni prijemnik) ---

@app.post("/generate-rival-strategy")
async def generate_rival_strategy(request: Request):
    # KORAK 1: Primi sirove podatke (šta god da sajt pošalje)
    try:
        raw_data = await request.json()

        print("\n--- PRIMLJENI PODACI SA SAJTA ---")
        print(json.dumps(raw_data, indent=2)) # Ovo će se ispisati u terminalu
        print("---------------------------------\n")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ne mogu da pročitam podatke: {e}")

    # Provera ključa
    if not GEMINI_API_KEY or "OVDE_IDE" in GEMINI_API_KEY:

         raise HTTPException(status_code=500, detail="API ključ nije unet u main.py!")

    # KORAK 2: Izvuci podatke "na silu" (tražimo i ugnježdene i ravne strukture)
    # Pokušavamo da nađemo podatke gde god da su
    my_prod = raw_data.get("my_product", {})
    comp_prod = raw_data.get("competitor", {})

    # Pravimo prompt od onoga što smo našli
    user_prompt = f"""
    MY PRODUCT INFO:
    Name: {my_prod.get('name') or raw_data.get('product_name') or "Unknown"}
    Price: {my_prod.get('price') or raw_data.get('price') or "Unknown"}
    Features: {my_prod.get('key_features') or raw_data.get('key_features') or "Unknown"}
    Weaknesses: {my_prod.get('weaknesses') or raw_data.get('weaknesses') or "Unknown"}
    Audience: {my_prod.get('target_audience') or raw_data.get('target_audience') or "Unknown"}
    
    COMPETITOR INFO:
    Name: {comp_prod.get('name') or raw_data.get('competitor_name') or "Unknown"}
    Price: {comp_prod.get('price') or raw_data.get('competitor_price') or "Unknown"}

    Features: {comp_prod.get('features') or raw_data.get('competitor_features') or "Unknown"}
    """

    system_prompt = """
    You are Rivally. Analyze the user's product vs competitor.
    Return ONLY valid JSON with this structure:
    {
        "dominance_score": "1-10 score",
        "winning_strategy": "3 step strategy",

        "fatherly_advice": "One harsh advice",
        "reality_check": {
            "threat_assessment": "Assessment text",
            "market_gaps_found": "Gaps text"
        }
    }
    """

    # KORAK 3: Pitaj AI
    try:
        response = await model.generate_content_async(
            contents=[

                {"role": "user", "parts": [{"text": system_prompt}, {"text": user_prompt}]}
            ]
        )
        
        text_response = response.text.strip()
        # Čišćenje JSON-a ako AI doda ```json oznake
        if "```" in text_response:
            text_response = text_response.split("```json")[-1].split("```")[0].strip()
            
        return json.loads(text_response)

    except Exception as e:
        print(f"AI GREŠKA: {e}")
        raise HTTPException(status_code=500, detail=f"Greška u AI generisanju: {e}")
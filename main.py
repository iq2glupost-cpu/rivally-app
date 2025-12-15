import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from supabase import create_client, Client
from typing import Any, Optional

# --- 1. KONFIGURACIJA ---


app = FastAPI(
    title="Rivally API (Global Edition)", 
    version="3.0 - The Money Maker"
)

# CORS (Dozvoljava da Frontend priča sa Backendom)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 🔑 POVEZIVANJE KLJUČEVA SA RENDERA 🔑 ---
# Server traži ključeve u "Environment Variables" na Renderu
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Optional[Client] = None


# --- INICIJALIZACIJA BAZA ---

# 1. Supabase (Za čuvanje E-mailova)
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase povezanim. Skupljamo leadove!")
    except Exception as e:
        print(f"⚠️ Supabase greška: {e}. Aplikacija će raditi, ali neće čuvati mailove.")
else:
    print("⚠️ Nema Supabase ključeva na Renderu. Preskačem bazu.")

# 2. Gemini AI (Motor)
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"⚠️ Gemini greška: {e}")

# Podešavanja za generisanje teksta
generation_config = {
    "temperature": 0.7, 
    "top_p": 0.95,
    "max_output_tokens": 4096,
    "response_mime_type": "application/json", # OBAVEZNO: Tera AI da vrati JSON
}

# --- 2. THE BRAIN (Sistem Instrukcije - OVO JE ONO ŠTO "GRMI") ---

SYSTEM_INSTRUCTION = """

You are RIVALLY - An elite competitive marketing strategist and a tough-love startup mentor from Silicon Valley.
Your goal is to help the user dominate their market. DO NOT be polite. Be effective.

YOUR TASK:
Analyze the user's product vs. the competitor.
Generate a JSON response containing 6 specific parts based on the input data.

JSON STRUCTURE & RULES:


1. "dominance_score" (Integer 0-100):
   - Calculate the real probability of winning the customer based on the data.
   - <40: Red zone (They are much stronger/cheaper).
   - 40-75: Yellow zone (Dogfight).
   - >75: Green zone (Total Domination).

2. "score_explanation" (String):
   - One short, punchy sentence in English explaining the score.

3. "reality_check" (Object):
   - "competitor_wins": List[String]. What does the rival do better? Be honest. (e.g., "Better UI", "Established Brand").
   - "improvements_needed": List[String]. What must the user fix/build ASAP?

4. "fatherly_advice" (String):
   - Direct mentorship to the USER (the business owner).
   - Tone: A veteran VC investor giving advice. Warm but firm. Use "Listen," "You need to," "We will win by...".

   - Language: English.

5. "html_content" (String):
   - **This is the Winning Strategy.** Provide a detailed, aggressive comparison and 3-step battle plan. 
   - Use aggressive US Copywriting (Direct, Benefit-driven).
   - CRITICAL: Use HTML tags like <p>, <strong>, <ul>, <li> for readability. Do NOT use Markdown.

6. "instagram_caption" (String):

   - A viral Instagram caption promoting the comparison.
   - Start with a Hook. Use Emojis (🔥, 🚀, 🛑). Use Hashtags.
   - Language: English.

IMPORTANT: Respond ONLY in valid JSON format.
"""

# Inicijalizacija Modela
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", # Najbrži i najstabilniji model
    

system_instruction=SYSTEM_INSTRUCTION,
)

# --- 3. MODELI PODATAKA (Ono što stiže sa sajta) ---

class ProductData(BaseModel):
    name: str
    price: str
    features: Any # Može biti lista ili tekst
    weaknesses: Optional[str] = None

class 

ComparisonRequest(BaseModel):
    my_product: ProductData
    competitor_product: ProductData
    target_audience: str
    client_email: str # OVO JE NOVO (Za bazu)

# --- 4. API ENDPOINT (Glavna funkcija) ---

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return 

FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(request: ComparisonRequest):
    
    # Sigurnosna provera
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY nije podešen na Renderu!")

    # Formatiranje podataka za AI

    my_features_str = ', '.join(request.my_product.features) if isinstance(request.my_product.features, list) else request.my_product.features
    comp_features_str = ', '.join(request.competitor_product.features) if isinstance(request.competitor_product.features, list) else request.competitor_product.features

    # Kreiranje Prompta (Na engleskom za bolji rezultat)

    user_prompt = f"""
    ANALYZE THIS BATTLE:
    
    ME (THE CLIENT):
    Product Name: {request.my_product.name}
    Price: {request.my_product.price}
    Key Features: {my_features_str}
    My Weaknesses/Fears: {request.my_product.weaknesses or "None stated"}

    THEM (THE RIVAL):
    Product Name: {request.competitor_product.name}
    Price: {request.competitor_product.price}
    Key Features: {comp_features_str}

    TARGET AUDIENCE: {request.target_audience}
    """

    try:
        # --- KORAK 1: Generisanje Strategije (AI) ---
        response = model.generate_content(
            user_prompt,
            generation_config=generation_config
        )
        
        # Parsiranje odgovora
        result_json = json.loads(response.text)

        # --- KORAK 2: Čuvanje u Bazu (Supabase) ---
        if supabase:
            try:
                # Upisujemo podatke u tabelu 'leads'
                supabase.table("leads").insert({
                    "email": request.client_email,
                    "product_name": request.my_product.name,
                    "competitor": request.competitor_product.name,
                    "score": result_json.get("dominance_score"),
                    "status": "new"
                }).execute()
                print(f"✅ Lead sačuvan: {request.client_email}")
            except Exception as e:
                # Ako baza pukne, ne rušimo sajt, samo ispišemo grešku u log
                print(f"⚠️ Nije uspelo čuvanje u bazu: {e}")
                
        # --- KORAK 3: Slanje Rezultata Korisniku ---
        return result_json

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        # Vraćamo detaljnu grešku da znamo šta nije u redu
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}")

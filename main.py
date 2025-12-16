import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from supabase import create_client, Client
from typing import Any, Optional

# --- KONFIGURACIJA ---


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ključevi sa Rendera / Vercela
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")

SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Optional[Client] = None

# Povezivanje na Supabase
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase povezan.")
    except Exception as e:

        print(f"⚠️ Supabase greška: {e}")

# Povezivanje na Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- MODELI ---

class ProductData(BaseModel):
    name: str
    price: str
    features: Any
    weaknesses: Optional[str] = None
    url: Optional[str] = None  # <--- NOVO: URL POLJE

class ComparisonRequest(BaseModel):
    my_product: ProductData
    competitor_product: ProductData
    target_audience: str
    
class LeadRequest(BaseModel):
    email: str
    score: int
    product_name: str

    competitor_name: str

# --- PROMPT I AI ---

SYSTEM_INSTRUCTION = """
You are RIVALLY - An elite competitive marketing strategist.
Your goal is to help the user dominate their market.

YOUR TASK:
Generate a JSON response containing 6 specific parts based on the input data.

JSON STRUCTURE:


1. "dominance_score" (Integer 0-100): Calculated probability of winning.
2. "score_explanation" (String): Short punchy sentence explaining the score.
3. "reality_check" (Object): { "competitor_wins": [List of strings], "improvements_needed": [List of strings] }
4. "fatherly_advice" (String): Direct mentorship advice.
5. "html_content" (String): The detailed strategy (HTML format 

with <p>, <strong>, <ul>).
6. "instagram_caption" (String): Viral social media caption.

IMPORTANT: Respond ONLY in valid JSON format.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-pro", 
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json"
    )
)

# --- ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse('index.html')

# 1. GENERISANJE ANALIZE

@app.post("/generate-rival-strategy")
async def generate_strategy(request: ComparisonRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Nedostaje API Key.")

    my_features = str(request.my_product.features)
    comp_features = str(request.competitor_product.features)
    

    # --- NOVO: Priprema URL-a za prompt ---
    comp_url_text = f", URL: {request.competitor_product.url}" if request.competitor_product.url else ""

    prompt = f"""
    ANALYZE:
    ME: {request.my_product.name}, {request.my_product.price}, {my_features}, Weakness: {request.my_product.weaknesses}


    RIVAL: {request.competitor_product.name}, {request.competitor_product.price}, {comp_features}{comp_url_text}
    AUDIENCE: {request.target_audience}
    
    If the RIVAL URL is provided, use it to infer their specific business model and industry positioning accurately.
    """

    try:
        # Generisanje odgovora
        response = model.generate_content(prompt)
        # Čišćenje i parsiranje JSON-a
        ai_output_text = response.text.strip()
        parsed_json = json.loads(ai_output_text)

        # --- ČUVANJE U SUPABASE ---
        if supabase:
            try:
                supabase.table("history").insert({
                    "business_name": request.my_product.name,
                    "ai_response": ai_output_text
                }).execute()
                print("✅ Analiza sačuvana u history tabelu.")
            except Exception as db_e:
                print(f"⚠️ Nije uspelo čuvanje u bazu: {db_e}")

        return parsed_json

    except Exception as e:
        print(f"AI Error: {e}")

        raise HTTPException(status_code=500, detail="Greška u AI analizi.")

# 2. ČUVANJE EMAILA
@app.post("/save-lead")
async def save_lead(request: LeadRequest):
    if not supabase:
        return {"status": "skipped", "message": "No database connected"}
    
    try:
        info_text = f"Lead Captured! Score: {request.score}, Competitor: {request.competitor_name}"
        
        supabase.table("history").insert({
            "business_name": request.product_name, 
            "email": request.email,                
            "ai_response": info_text               
        }).execute()
        
        return {"status": "success", "message": "Email sačuvan!"}

    except Exception as e:
        print(f"DB Error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/test-gemini")
def test_gemini():
    try:
        modeli = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modeli.append(m.name)
        
        return {

            "STATUS": "Uspesno povezan",
            "DOSTUPNI_MODELI": modeli
        }
    except Exception as e:
        return {"GRESKA": str(e)}

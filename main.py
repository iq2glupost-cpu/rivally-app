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

# Ključevi sa Rendera
GEMINI_API_KEY = 'AIzaSyCc0YILD8qQv2pyA5GDBzPNPcHcj9NpevU'
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


class ComparisonRequest(BaseModel):
    my_product: ProductData
    competitor_product: ProductData
    target_audience: str
    # Email više nije obavezan za generisanje!
    
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
1. "dominance_score" (Integer 

0-100): Calculated probability of winning.
2. "score_explanation" (String): Short punchy sentence explaining the score.
3. "reality_check" (Object): { "competitor_wins": [List of strings], "improvements_needed": [List of strings] }
4. "fatherly_advice" (String): Direct mentorship advice.
5. "html_content" (String): The detailed strategy (HTML format with <p>, <strong>, <ul>).
6. "instagram_caption" (String): 

Viral social media caption.

IMPORTANT: Respond ONLY in valid JSON format.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION,
)

# --- ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse('index.html')

# 1. GENERISANJE ANALIZE (Ne traži email, vraća rezultat)
@app.post("/generate-rival-strategy")
async def generate_strategy(request: ComparisonRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Nedostaje API Key.")

    my_features = str(request.my_product.features)
    comp_features = str(request.competitor_product.features)

    prompt = f"""
    ANALYZE:
    ME: {request.my_product.name}, {request.my_product.price}, {my_features}, Weakness: {request.my_product.weaknesses}

    RIVAL: {request.competitor_product.name}, {request.competitor_product.price}, {comp_features}
    AUDIENCE: {request.target_audience}
    """

    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"AI Error: {e}")

        raise HTTPException(status_code=500, detail="Greška u AI analizi.")

# 2. ČUVANJE EMAILA (Ovo se zove kad kliknu "Unlock")
@app.post("/save-lead")
async def save_lead(request: LeadRequest):
    if not supabase:
        return {"status": "skipped", "message": "No database connected"}
    
    try:
        supabase.table("leads").insert({
            "email": request.email,
            "product_name": request.product_name,
            "competitor": request.competitor_name,
            "score": request.score,
            "status": "unlocked"
        }).execute()
        return {"status": "success"}
    except Exception as e:
        print(f"DB Error: {e}")
        return {"status": "error", "message": str(e)}

# --- OVO JE DETEKTIV ---
@app.get("/test-gemini")
def test_gemini():
    try:
        modeli = []
        # Pitamo Google sta ima na raspolaganju za ovaj kljuc
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modeli.append(m.name)
        
        return {
            "STATUS": "Uspesno povezan",

            "TVOJ_KLJUC_VIDI_OVE_MODELE": modeli
        }
    except Exception as e:
        return {"GRESKA_SA_GOOGLEOM": str(e)}
















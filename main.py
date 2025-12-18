import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from supabase import create_client, Client
from typing import Any, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# KONFIGURACIJA (Učitava se sa Vercel Settings)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except: pass

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# MODELI (Prilagođeni tvom originalnom kodu)
class ProductData(BaseModel):
    name: str
    url: Optional[str] = None
    price: Optional[str] = "N/A"
    features: Any = "N/A"

class ComparisonRequest(BaseModel):
    my_product: ProductData
    competitor_product: ProductData
    target_audience: Optional[str] = "General Market"

class LeadRequest(BaseModel):
    email: str
    score: int
    product_name: str
    competitor_name: str

# KORISTI MODEL KOJI TI JE RADIO (npr. gemini-1.5-pro ili flash)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

@app.post("/generate-rival-strategy")
async def generate_strategy(request: ComparisonRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="API Key missing")

    prompt = f"Analyze market battle: {request.my_product.url} vs {request.competitor_product.url}. Output JSON with dominance_score, score_explanation, reality_check (object), and html_content."

    try:
        response = model.generate_content(prompt)
        # Čišćenje JSON-a od AI dodataka
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-lead")
async def save_lead(request: LeadRequest):
    if supabase:
        try:
            supabase.table("history").insert({
                "business_name": request.product_name,
                "email": request.email,
                "ai_response": f"Captured Score: {request.score}"
            }).execute()
        except: pass
    return {"status": "ok"}

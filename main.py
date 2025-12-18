import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
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

# KONFIGURACIJA
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase povezan.")
    except Exception as e:
        print(f"⚠️ Supabase greška: {e}")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# MODELI
class ProductData(BaseModel):
    name: str
    price: str
    features: Any
    weaknesses: Optional[str] = None
    url: Optional[str] = None

class ComparisonRequest(BaseModel):
    my_product: ProductData
    competitor_product: ProductData
    target_audience: str
   
class LeadRequest(BaseModel):
    email: str
    score: int
    product_name: str
    competitor_name: str

# SYSTEM PROMPT
SYSTEM_INSTRUCTION = """
You are RIVALLY - An elite competitive marketing strategist.
Your goal is to help the user dominate their market.
Output valid JSON only.
"""

# KORISTIMO MODEL KOJI SI TRAŽIO
model = genai.GenerativeModel(
    model_name="gemini-2.5-pro",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json"
    )
)

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(request: ComparisonRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Nedostaje API Key.")

    comp_url_text = f", URL: {request.competitor_product.url}" if request.competitor_product.url else ""
    prompt = f"""
    ANALYZE battle:
    ME: {request.my_product.name}, {request.my_product.price}, {request.my_product.features}, Weakness: {request.my_product.weaknesses}
    RIVAL: {request.competitor_product.name}, {request.competitor_product.price}, {request.competitor_product.features}{comp_url_text}
    AUDIENCE: {request.target_audience}
    """

    try:
        response = model.generate_content(prompt)
        ai_output_text = response.text.strip()
        parsed_json = json.loads(ai_output_text)

        if supabase:
            try:
                supabase.table("history").insert({
                    "business_name": request.my_product.name,
                    "ai_response": ai_output_text
                }).execute()
            except: pass

        return parsed_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-lead")
async def save_lead(request: LeadRequest):
    if not supabase:
        return {"status": "skipped"}
    try:
        supabase.table("history").insert({
            "business_name": request.product_name,
            "email": request.email,               
            "ai_response": f"Captured lead for {request.competitor_name}"              
        }).execute()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

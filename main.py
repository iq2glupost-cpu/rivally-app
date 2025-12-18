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

# --- CONFIG ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Supabase Connection

supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        pass

# Gemini Connection
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


# --- MODELS ---
class ProductData(BaseModel):
    name: str
    price: Optional[str] = "N/A"
    features: Any
    url: Optional[str] = None

class ComparisonRequest(BaseModel):
    my_product: ProductData
    competitor_product: ProductData
    target_audience: Optional[str] = "General Market"


class LeadRequest(BaseModel):
    email: str
    score: int
    product_name: str
    competitor_name: str

# --- AI LOGIC ---
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", 
    generation_config={"response_mime_type": "application/json"}
)

@app.post("/generate-rival-strategy")
async def generate_strategy(request: ComparisonRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="API Key Missing")

    prompt = f"""
    Analyze battle: {request.my_product.url} vs {request.competitor_product.url}. 
    Return valid JSON with: dominance_score (0-100), score_explanation, 
    reality_check (competitor_wins, improvements_needed), html_content.
    """

    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        return {
            "dominance_score": 0,

            "score_explanation": "AI Service Error",
            "reality_check": {"competitor_wins": [], "improvements_needed": []},
            "html_content": f"<p>Error: {str(e)}</p>"
        }

@app.post("/save-lead")
async def save_lead(request: LeadRequest):
    if supabase:
        try:
            supabase.table("history").insert({

                "business_name": request.product_name,
                "email": request.email,
                "ai_response": f"Score: {request.score}"
            }).execute()
        except:
            pass
    return {"status": "ok"}

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

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"DB Warning: {e}")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", # Tvoj model
    generation_config={"response_mime_type": "application/json"}
)

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(request: ComparisonRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="API Key missing")
   
    # Prompt ostaje isti kako bi AI znao format
    prompt = f"Analyze market battle: {request.my_product.name} vs {request.competitor_product.name}. Output JSON report."

    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-lead")
async def save_lead(request: LeadRequest):
    if supabase:
        try:
            supabase.table("history").insert({
                "business_name": request.product_name,
                "email": request.email,               
                "ai_response": f"Captured lead for {request.competitor_name}"              
            }).execute()
        except: pass
    return {"status": "success"}

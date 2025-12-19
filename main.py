import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from supabase import create_client, Client

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

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None
if GEMINI_API_KEY: genai.configure(api_key=GEMINI_API_KEY)

class ProductData(BaseModel):
    name: str
    url: str
    features: str
    price: str

class ComparisonRequest(BaseModel):
    my_product: ProductData
    competitor_product: ProductData
    target_audience: str

# AI INSTRUCTIONS FOR TEASER & HOOK
SYSTEM_INSTRUCTION = """
You are RIVALLY - An elite market strategist.
Return ONLY valid JSON.
'score_explanation' MUST be a provocative, punchy 1-2 sentence teaser that makes the user want to see the full report.
'html_content' MUST be the comprehensive strategic audit in HTML format.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-pro",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config={"response_mime_type": "application/json"}
)

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(request: ComparisonRequest):
    prompt = f"Analyze: {request.my_product} vs {request.competitor_product} for audience: {request.target_audience}."
    try:
        response = model.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except: raise HTTPException(status_code=500)

@app.post("/save-lead")
async def save_lead(data: dict):
    if supabase:
        try:
            supabase.table("history").insert({
                "business_name": data['product_name'],
                "email": data['email'],
                "ai_response": f"Score: {data['score']} vs {data['competitor_name']}"
            }).execute()
        except: pass
    return {"status": "success"}

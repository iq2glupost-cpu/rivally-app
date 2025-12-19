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

# ENV
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None
if GEMINI_API_KEY: genai.configure(api_key=GEMINI_API_KEY)

class ComparisonRequest(BaseModel):
    my_product: dict
    competitor_product: dict
    target_audience: str

# SYSTEM INSTRUCTIONS
SYSTEM_INSTRUCTION = """
You are RIVALLY - An elite competitive marketing strategist.
Output ONLY JSON.
Fields:
1. 'dominance_score': integer (0-100)
2. 'score_explanation': A sharp, 1-2 sentence teaser that points out a critical weakness or opportunity to pique interest.
3. 'html_content': The full, deep-dive strategic report in HTML.
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
async def generate_strategy(data: dict):
    prompt = f"Battle: {data['my_product']} vs {data['competitor_product']}. Strategic Teaser + Full Audit."
    try:
        response = model.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except: raise HTTPException(status_code=500)

@app.post("/save-lead")
async def save_lead(data: dict):
    if supabase:
        try:
            supabase.table("history").insert({"business_name": data['product_name'], "email": data['email']}).execute()
        except: pass
    return {"status": "success"}

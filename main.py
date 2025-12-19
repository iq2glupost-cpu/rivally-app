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

# INSTRUKCIJE ZA DUBOKI IZVEŠTAJ
SYSTEM_INSTRUCTION = """
You are RIVALLY - An elite competitive marketing strategist.
YOUR OUTPUT MUST BE ONLY VALID JSON.

1. 'dominance_score': (0-100)
2. 'score_explanation': A sharp, 1-2 sentence teaser. Identify ONE SPECIFIC critical weakness or high-value opportunity in the market battle that would immediately shock or intrigue the user.
3. 'html_content': A VERY LONG, DEEP-DIVE STRATEGIC REPORT. Include SWOT, detailed feature comparison, content gap analysis, SEO positioning, and a 3-step action plan for total market dominance.
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
    prompt = f"Battle Analysis: {data['my_product']} vs {data['competitor_product']}. Strategic scan for dominance."
    try:
        response = model.generate_content(prompt)
        # Čišćenje JSON-a za stabilnost
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
                "ai_response": f"Audit Unlocked: {data['score']}% vs {data['competitor_name']}"
            }).execute()
        except: pass
    return {"status": "success"}

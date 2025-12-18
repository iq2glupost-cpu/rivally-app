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

# MODELI PODATAKA
class ProductData(BaseModel):
    name: str
    price: Optional[str] = "N/A"
    features: Any
    weaknesses: Optional[str] = None
    url: Optional[str] = None # Dodat URL i za tvoj proizvod

class 

ComparisonRequest(BaseModel):
    my_product: ProductData
    competitor_product: ProductData
    target_audience: Optional[str] = "General Market" # Opcionalno

class LeadRequest(BaseModel):
    email: str
    score: int
    product_name: str
    competitor_name: str

# SYSTEM PROMPT
SYSTEM_INSTRUCTION = """

You are RIVALLY - An elite competitive marketing strategist.
Your goal is to help the user dominate their market.

YOUR TASK:
Analyze the two URLs/Products provided. 
If URLs are present, infer the business model, pricing strategy, and features from the domain context.

Generate a JSON response containing 6 specific parts:
1. "dominance_score" (Integer 

0-100): Probability of User winning against Rival.
2. "score_explanation" (String): Short punchy sentence explaining the score.
3. "reality_check" (Object): { "competitor_wins": [List of strings], "improvements_needed": [List of strings] }
4. "fatherly_advice" (String): Direct mentorship advice.
5. "html_content" (String): The detailed strategy (HTML format with <p>, <strong>, <ul>). Make it look like a classified report.

6. "instagram_caption" (String): Viral social media caption.

IMPORTANT: Respond ONLY in valid JSON format.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", 
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json"
    )
)

# RUTE

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(request: ComparisonRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Nedostaje API Key.")

    # Priprema podataka za AI
    my_info = f"NAME: {request.my_product.name}"
    if request.my_product.url:
        my_info += f", URL: {request.my_product.url}"
    
    comp_info = f"NAME: {request.competitor_product.name}"
    if request.competitor_product.url:
        comp_info += f", URL: {request.competitor_product.url}"

    prompt = f"""
    ANALYZE BATTLE:
    [ME - THE USER]: {my_info}
    [THE RIVAL]: {comp_info}
    
    CONTEXT: The user wants to know how to beat this specific competitor. 
    Use the URLs to deduce the industry and specific weaknesses.
    """

    try:
        response = model.generate_content(prompt)
        ai_output_text = response.text.strip()
        parsed_json = json.loads(ai_output_text)

        # Logovanje u Supabase (ako je povezan)
        if supabase:
            try:
                supabase.table("history").insert({
                    "business_name": request.my_product.name,
                    "ai_response": ai_output_text
                }).execute()
            except Exception:
                pass

        return parsed_json

    except Exception as e:
        print(f"AI Error: {e}")
        raise HTTPException(status_code=500, detail="Greška u AI analizi.")


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
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

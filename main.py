import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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

# --- ENVIRONMENT VARIABLES ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# SMTP SETUP (Moraš uneti ovo u Vercel Environment Variables)
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")

# --- CONNECTIONS ---
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Supabase Init Error: {e}")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- MODELS ---
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
    report_html: Optional[str] = ""

# --- AI MODEL ---
SYSTEM_INSTRUCTION = """
You are RIVALLY - An elite competitive marketing strategist.
Output valid JSON only.
Structure: dominance_score (int), score_explanation (str), reality_check (obj), html_content (str).
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config=genai.GenerationConfig(response_mime_type="application/json")
)

# --- EMAIL FUNCTION ---
def send_strategic_email(target_email, report_content, score, competitor):
    if not SMTP_USER or not SMTP_PASS:
        return print("⚠️ Email skipped: SMTP credentials missing.")
   
    msg = MIMEMultipart()
    msg["Subject"] = f"RIVALLY INTELLIGENCE: Score {score}/100 vs {competitor}"
    msg["From"] = f"RIVALLY AI <{SMTP_USER}>"
    msg["To"] = target_email

    body = f"""
    <div style="background:#000; color:#fff; padding:30px; font-family:sans-serif;">
        <h2 style="color:#3b82f6; letter-spacing:2px;">STRATEGIC AUDIT COMPLETE</h2>
        <h1 style="font-size:40px; margin:10px 0;">{score}/100</h1>
        <hr style="border-color:#333;">
        <div style="color:#ccc; line-height:1.6;">{report_content}</div>
        <p style="margin-top:30px; font-size:10px; color:#555;">POWERED BY SAKORP HOLDING</p>
    </div>
    """
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            print(f"✅ Email sent to {target_email}")
    except Exception as e:
        print(f"⚠️ Email Error: {e}")

# --- ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(request: ComparisonRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="API Key Missing")

    prompt = f"Battle: {request.my_product.name} vs {request.competitor_product.name} (URL: {request.competitor_product.url}). Strategy report JSON."

    try:
        response = model.generate_content(prompt)
        ai_data = json.loads(response.text)
       
        if supabase:
            try:
                supabase.table("history").insert({
                    "business_name": request.my_product.name,
                    "ai_response": response.text
                }).execute()
            except: pass

        return ai_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-lead")
async def save_lead(request: LeadRequest):
    # 1. DB Save
    if supabase:
        try:
            supabase.table("history").insert({
                "business_name": request.product_name,
                "email": request.email,               
                "ai_response": f"Report sent for {request.competitor_name}"              
            }).execute()
        except: pass

    # 2. Send Email
    send_strategic_email(request.email, request.report_html, request.score, request.competitor_name)
   
    return {"status": "success"}


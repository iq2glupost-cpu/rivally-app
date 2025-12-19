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

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- CONFIGURATION ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None
if GEMINI_API_KEY: genai.configure(api_key=GEMINI_API_KEY)

# --- ELITE STRATEGIC INSTRUCTIONS (100% ENGLISH) ---
SYSTEM_INSTRUCTION = """
You are RIVALLY - SAKORP's elite strategic warfare engine.
Analyze the battle between Target Alpha (User) and Target Beta (Rival).
YOUR OUTPUT MUST BE ONLY VALID JSON.

STRUCTURE FOR 'free_sections' (UI Cards):
1. strategic_overview: High-level market landscape summary (📊).
2. product_audit: Brutally honest opinion on Alpha's current product/market fit (🧠).
3. tactical_tweaks: A list of 3 specific, low-effort high-impact changes (⚡). Return as an ARRAY of strings.

STRUCTURE FOR 'premium_report' (Email Only):
- This is the Master File. Deep-dive tactical audit.
- Include SWOT, psychological warfare hooks, and the KILL-SHOT move.
- 24-Month Forecast.
Use professional icons and clean HTML formatting.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-pro",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config={"response_mime_type": "application/json"}
)

def send_beta_report(target_email, premium_content, score, competitor):
    if not SMTP_USER: return
    msg = MIMEMultipart()
    msg["Subject"] = f"RIVALLY MASTER FILE: {score}% vs {competitor} (BETA ACCESS)"
    msg["From"] = f"SAKORP RIVALLY <{SMTP_USER}>"
    msg["To"] = target_email
   
    body = f"""
    <div style="background:#000; color:#fff; padding:40px; font-family:sans-serif; border:1px solid #2563eb;">
        <h1 style="color:#2563eb; text-transform:uppercase;">Strategic Master File Unlocked</h1>
        <h2 style="font-size:42px; margin:10px 0;">{score}% Dominance Index</h2>
        <p style="color:#888;">This is your restricted Beta Phase intelligence report.</p>
        <hr style="border:0; border-top:1px solid #333; margin:20px 0;">
        <div style="color:#ccc; line-height:1.6; font-size:16px;">{premium_content}</div>
        <p style="margin-top:40px; font-size:10px; color:#444;">RESTRICTED ACCESS // SAKORP HOLDING SYSTEMS &copy; 2025</p>
    </div>
    """
    msg.attach(MIMEText(body, "html"))
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except: pass

@app.get("/", response_class=HTMLResponse)
async def read_index(): return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(data: dict):
    prompt = f"Battle: {data['my_product']} vs {data['competitor_product']}. Generate Strategic Overview, Product Audit, and Master File."
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text.replace('```json', '').replace('```', '').strip())
    except: raise HTTPException(status_code=500)

@app.post("/save-lead")
async def save_lead(data: dict):
    if supabase:
        try:
            supabase.table("history").insert({"business_name": data['product_name'], "email": data['email']}).execute()
        except: pass
    send_beta_report(data['email'], data['premium_content'], data['score'], data['competitor_name'])
    return {"status": "success"}

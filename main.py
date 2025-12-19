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

# --- KONFIGURACIJA (Vercel Env Variables) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER") # Tvoj Gmail
SMTP_PASS = os.environ.get("SMTP_PASS") # App Password

# Inicijalizacija servisa
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None
if GEMINI_API_KEY: genai.configure(api_key=GEMINI_API_KEY)

# --- MODELI PODATAKA ---
class ComparisonRequest(BaseModel):
    my_product: dict
    competitor_product: dict
    target_audience: str

# --- AI INSTRUKCIJE ZA FREEMIUM MODEL ---
SYSTEM_INSTRUCTION = """
You are RIVALLY - SAKORP's elite strategic warfare engine.
Analyze the battle between Target Alpha (User) and Target Beta (Rival).
YOUR OUTPUT MUST BE ONLY VALID JSON.

STRUCTURE FOR 'free_sections' (Visible on website):
1. intro: High-level market overview (📊).
2. opinion: Bold, critical opinion on Alpha's current market standing (🧠).
3. improvements: Exactly 3 minor "Quick Wins" to show competence (⚡).

STRUCTURE FOR 'premium_report' (Sent to email only):
- This must be a MASSIVE, DEEP-DIVE tactical audit.
- Include full SWOT, SEO maps, and psychological sales hooks.
- THE KILL-SHOT: One brutal strategic move to eliminate Beta.
- 24-Month Forecast: Future of the market.
- Use professional icons, bold HTML tags, and clean spacing.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-pro",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config={"response_mime_type": "application/json"}
)

def send_master_report(target_email, premium_content, score, competitor):
    if not SMTP_USER or not SMTP_PASS: return
    msg = MIMEMultipart()
    msg["Subject"] = f"PREMIUM STRATEGIC AUDIT: {score}% vs {competitor}"
    msg["From"] = f"SAKORP RIVALLY <{SMTP_USER}>"
    msg["To"] = target_email
   
    body = f"""
    <div style="background:#000; color:#fff; padding:40px; font-family:sans-serif; border:1px solid #2563eb;">
        <h1 style="color:#2563eb; text-transform:uppercase;">Master Strategy Unlocked</h1>
        <h2 style="font-size:48px; margin:10px 0;">{score}% Dominance Index</h2>
        <hr style="border:0; border-top:1px solid #333; margin:20px 0;">
        <div style="color:#ccc; line-height:1.6; font-size:16px;">{premium_content}</div>
        <p style="margin-top:40px; font-size:10px; color:#444;">CONFIDENTIAL // SAKORP HOLDING SYSTEMS &copy; 2025</p>
    </div>
    """
    msg.attach(MIMEText(body, "html"))
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except Exception as e: print(f"SMTP Error: {e}")

@app.get("/", response_class=HTMLResponse)
async def read_index(): return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(data: dict):
    prompt = f"Battle: {data['my_product']} vs {data['competitor_product']}. Generate free preview and premium master-file."
    try:
        response = model.generate_content(prompt)
        # Čišćenje JSON-a
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"AI Error: {e}")
        raise HTTPException(status_code=500)

@app.post("/save-lead")
async def save_lead(data: dict):
    # 1. Čuvanje u bazu (Supabase)
    if supabase:
        try:
            supabase.table("history").insert({"business_name": data['product_name'], "email": data['email']}).execute()
        except: pass
   
    # 2. Slanje punog izveštaja (Simuliramo premium slanje nakon unosa mejla za sada)
    send_master_report(data['email'], data['premium_content'], data['score'], data['competitor_name'])
    return {"status": "success"}

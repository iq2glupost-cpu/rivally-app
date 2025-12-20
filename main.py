import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from google import genai

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- CORE CONFIG ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SMTP_USER = os.environ.get("SMTP_USER") # sakorp.rivally@gmail.com
SMTP_PASS = os.environ.get("SMTP_PASS")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# --- THE ELITE MASTER TEMPLATE ---
def send_elite_report(target_email, premium_content, score, competitor):
    if not SMTP_USER or not SMTP_PASS: return
  
    # OSIGURANJE: Email uvek ide malim slovima
    target_email = target_email.strip().lower()
  
    msg = MIMEMultipart()
    msg["Subject"] = f"CLASSIFIED: Strategic Intelligence Briefing | Dominance: {score}%"
    msg["From"] = f"SAKORP CORPORATION <{SMTP_USER}>"
    msg["To"] = target_email
  
    body = f"""
    <html>
    <body style="margin: 0; padding: 0; background-color: #f4f4f4; font-family: Arial, sans-serif;">
        <div style="padding: 40px; background-color: #000; color: #fff; text-align: center;">
            <h1 style="margin: 0;">SAKORP <span style="color: #2563eb;">CORPORATION</span></h1>
            <p style="font-size: 10px; letter-spacing: 2px;">CONFIDENTIAL REPORT: {score}% DOMINANCE</p>
        </div>
        <div style="padding: 40px; background-color: #fff;">
            <h2 style="color: #000;">Executive Neural Audit vs {competitor}</h2>
            <div style="line-height: 1.6; color: #333;">
                {premium_content}
            </div>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(body, "html"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            print(f"SUCCESS: Report sent to {target_email}")
    except Exception as e:
        print(f"SMTP ERROR: {e}")

# --- AI INSTRUCTIONS ---
SYSTEM_INSTRUCTION = """
You are RIVALLY - SAKORP's chief intelligence officer. Output VALID JSON.
FIELDS: dominance_score (int), score_explanation (str), free_hook (str), premium_report (HTML str).
"""

@app.get("/", response_class=HTMLResponse)
async def read_index(): return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(data: dict):
    prompt = f"Battle: {data['my_product']} vs {data['competitor_product']}. Target Audience: {data['target_audience']}."
    try:
        response = client.models.generate_content(
            model="gemini-2.0-pro-exp-02-05",
            contents=prompt,
            config={
                "system_instruction": SYSTEM_INSTRUCTION,
                "response_mime_type": "application/json",
                "temperature": 0.2
            }
        )
        # Čišćenje JSON-a da ne bi bilo "undefined" na frontu
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except: raise HTTPException(status_code=500)

@app.post("/save-lead")
async def save_lead(data: dict):
    # Uzimamo podatke iz zahteva (pazi na nazive ključeva)
    email = data.get('email', '').strip().lower() # Automatski popravlja velika slova
    content = data.get('premium_content', '')
    score = data.get('score', 0)
    competitor = data.get('competitor_name', 'Competitor')

    # 1. Šaljemo mejl
    if email:
        send_elite_report(email, content, score, competitor)
   
    return {"status": "success"}

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from supabase import create_client

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- CONFIG ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None
if GEMINI_API_KEY: genai.configure(api_key=GEMINI_API_KEY)

# --- STRICT FREEMIUM PROMPT ---
SYSTEM_INSTRUCTION = """
You are RIVALLY - SAKORP's elite strategic engine.
YOUR OUTPUT MUST BE ONLY VALID JSON.

1. dominance_score: integer (1-100). Be consistent based on the provided names.
2. score_teaser: A sharp, 1-sentence teaser.
3. free_hook: ONE short paragraph (max 3 sentences). Analyze the CORE conflict but DO NOT provide solutions.
4. premium_report: The FULL Master File (HTML format).
   - Sections: KILL-SHOT MOVE, SWOT, 24-MONTH FORECAST, CONTENT ROADMAP.
   - Use bold headers, professional icons, and a military-style tone.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-pro",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config={"response_mime_type": "application/json", "temperature": 0.2} # Niska temperatura za konzistentnost
)

@app.post("/generate-rival-strategy")
async def generate_strategy(data: dict):
    prompt = f"Analyze: {data['my_product']['name']} vs {data['competitor_product']['name']}."
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text.replace('```json', '').replace('```', '').strip())
    except: raise HTTPException(status_code=500)

@app.post("/save-lead")
async def save_lead(data: dict):
    if supabase:
        try: supabase.table("history").insert({"business_name": data['product_name'], "email": data['email']}).execute()
        except: pass
   
    # Slanje na mejl
    if SMTP_USER:
        msg = MIMEMultipart()
        msg["Subject"] = f"RIVALLY MASTER FILE: {data['score']}% Dominance Unlocked"
        msg["From"] = f"SAKORP RIVALLY <{SMTP_USER}>"
        msg["To"] = data['email']
        msg.attach(MIMEText(f"<html><body style='background:#000;color:#fff;padding:30px;'>{data['premium_content']}</body></html>", "html"))
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls(); server.login(SMTP_USER, SMTP_PASS); server.send_message(msg)
        except: pass
    return {"status": "success"}

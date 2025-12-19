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
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASSWORD") # Proveri da li se na Vercelu zove SMTP_PASSWORD
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

# Inicijalizacija Supabase klijenta
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- THE ELITE MASTER TEMPLATE ---
def send_master_report(target_email, premium_content, score, competitor):
    if not SMTP_USER or not SMTP_PASS:
        print("SMTP Credentials missing")
        return
  
    msg = MIMEMultipart()
    msg["Subject"] = f"CLASSIFIED: Strategic Intelligence Briefing | Dominance: {score}%"
    msg["From"] = f"SAKORP CORPORATION <{SMTP_USER}>"
    msg["To"] = target_email
  
    body = f"""
    <html>
    <body style="background-color: #000; color: #fff; font-family: Arial, sans-serif; padding: 40px;">
        <h1 style="color: #2563eb;">SAKORP MASTER FILE</h1>
        <p>Dominance Quotient: {score}% vs {competitor}</p>
        <div style="border-top: 1px solid #333; padding-top: 20px;">
            {premium_content}
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
            print("Email sent successfully")
    except Exception as e:
        print(f"Email error: {e}")

# --- AI SETUP ---
SYSTEM_INSTRUCTION = "You are RIVALLY - SAKORP officer. Output JSON: dominance_score, score_explanation, tactical_breach, premium_report (HTML)."

model = genai.GenerativeModel(
    model_name="gemini-2.5-pro", 
    system_instruction=SYSTEM_INSTRUCTION
)

@app.post("/generate-rival-strategy")
async def generate_strategy(data: dict):
    prompt = f"Battle: {data['my_product']['name']} vs {data['competitor_product']['name']}."
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-lead")
async def save_lead(data: dict):
    # Logika za bazu
    if supabase:
        try:
            supabase.table("history").insert({
                "business_name": data.get('product_name'),
                "email": data.get('email')
            }).execute()
        except Exception as e: print(f"DB Error: {e}")
  
    # Logika za slanje
    send_master_report(
        data['email'],
        data.get('premium_content', 'No content generated'),
        data.get('score', 0),
        data.get('competitor_name', 'Rival')
    )
    return {"status": "success"}

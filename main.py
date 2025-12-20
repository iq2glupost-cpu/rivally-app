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

# Middleware mora biti ovde
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- KONFIGURACIJA ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")

# Inicijalizacija klijenta - SIGURNA VERZIJA
def get_client():
    if not GEMINI_API_KEY:
        return None
    return genai.Client(api_key=GEMINI_API_KEY)

# --- FUNKCIJA ZA MEJL ---
def send_elite_report(target_email, premium_content, score, competitor):
    if not SMTP_USER or not SMTP_PASS:
        print("SMTP Error: Podaci nisu u Vercelu")
        return
  
    clean_email = target_email.strip().lower()
    msg = MIMEMultipart()
    msg["Subject"] = f"CLASSIFIED: Strategic Intelligence Briefing | Dominance: {score}%"
    msg["From"] = f"SAKORP CORPORATION <{SMTP_USER}>"
    msg["To"] = clean_email
  
    body = f"""
    <html>
    <body style="background:#000; color:#fff; font-family:Arial; padding:40px;">
        <h1 style="color:#2563eb;">SAKORP INTELLIGENCE</h1>
        <p>Report for: {clean_email}</p>
        <p>Score vs {competitor}: <strong>{score}%</strong></p>
        <hr style="border-color:#2563eb;">
        <div style="color:#ccc;">{premium_content}</div>
    </body>
    </html>
    """
    msg.attach(MIMEText(body, "html"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except Exception as e:
        print(f"Mejl nije poslat: {e}")

# --- RUTE ---

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(data: dict):
    client = get_client()
    if not client:
        raise HTTPException(status_code=500, detail="AI Client Error")

    my_p = data.get('my_product', {})
    comp_p = data.get('competitor_product', {})
   
    prompt = f"Analyze Battle: {my_p.get('name')} vs {comp_p.get('name')}. Audience: {data.get('target_audience')}."
   
    system_instruction = """
    You are RIVALLY officer. Output VALID JSON ONLY.
    Structure:
    {
      "dominance_score": int,
      "score_explanation": "str",
      "tactical_breach": "str",
      "premium_report": "HTML str"
    }
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-pro-exp-02-05",
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "temperature": 0.2
            }
        )
        # Ciscenje odgovora
        res_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(res_text)
    except Exception as e:
        print(f"AI Error: {e}")
        # Sigurnosni povratni podaci da front ne pukne
        return {
            "dominance_score": 0,
            "score_explanation": "Neural Link Timeout.",
            "tactical_breach": "System offline.",
            "premium_report": ""
        }

@app.post("/save-lead")
async def save_lead(data: dict):
    email = data.get('email')
    if email:
        send_elite_report(
            email,
            data.get('premium_content', ''),
            data.get('score', 0),
            data.get('competitor_name', 'Target')
        )
    return {"status": "success"}

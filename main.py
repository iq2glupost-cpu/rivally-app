import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
# Koristimo novu google-genai biblioteku (mora biti u requirements.txt)
from google import genai

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- CORE CONFIG ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")

# Inicijalizacija novog klijenta
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# --- THE ELITE MASTER TEMPLATE ---
def send_elite_report(target_email, premium_content, score, competitor):
    if not SMTP_USER or not SMTP_PASS:
        return
  
    msg = MIMEMultipart()
    msg["Subject"] = f"CLASSIFIED: Strategic Intelligence Briefing | Dominance: {score}%"
    msg["From"] = f"SAKORP CORPORATION <{SMTP_USER}>"
    msg["To"] = target_email
  
    body = f"""
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@400;700&display=swap');
        </style>
    </head>
    <body style="margin: 0; padding: 0; background-color: #f4f4f4; font-family: 'Inter', Arial, sans-serif;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="padding: 40px 0;">
            <tr>
                <td align="center">
                    <table width="650" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border: 1px solid #dddddd; position: relative; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.05);">
                        <tr>
                            <td style="padding: 40px; background-color: #000000; color: #ffffff;">
                                <table width="100%" border="0">
                                    <tr>
                                        <td>
                                            <div style="font-size: 10px; letter-spacing: 5px; text-transform: uppercase; color: #2563eb; font-weight: bold; margin-bottom: 5px;">Classified Strategic Asset</div>
                                            <div style="font-family: 'Playfair Display', serif; font-size: 28px; font-weight: bold; letter-spacing: -1px;">SAKORP <span style="color: #2563eb;">CORPORATION</span></div>
                                        </td>
                                        <td align="right" style="font-size: 10px; color: #666; font-family: monospace;">
                                            DOC_REF: INTEL-{score}-2025<br>STRICTLY CONFIDENTIAL
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 50px;">
                                <div style="text-align: center; margin-bottom: 50px;">
                                    <div style="font-size: 110px; font-weight: 900; color: #000; line-height: 1; letter-spacing: -5px;">{score}<span style="font-size: 40px; color: #2563eb;">%</span></div>
                                    <div style="font-size: 12px; font-weight: bold; color: #999; text-transform: uppercase; letter-spacing: 6px;">Market Dominance Quotient</div>
                                </div>
                                <div style="font-size: 15px; color: #333; line-height: 1.9;">
                                    {premium_content}
                                </div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
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
        print(f"Email error: {e}")

# --- AI INSTRUCTIONS ---
SYSTEM_INSTRUCTION = """
You are RIVALLY - SAKORP's chief intelligence officer. Output VALID JSON ONLY.
TONE: Institutional, precise, brutal.

FIELDS:
1. dominance_score (int)
2. score_explanation (string)
3. free_hook (string)
4. premium_report (HTML string)
"""

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(data: dict):
    if not client:
        raise HTTPException(status_code=500, detail="AI Client not configured")
       
    prompt = f"Battle: {data.get('my_product')} vs {data.get('competitor_product')}. Target Audience: {data.get('target_audience')}."
   
    try:
        # Poziv Gemini 2.5 Pro modela (ili 2.0 zavisno od dostupnosti)
        response = client.models.generate_content(
            model="gemini-2.0-pro-exp-02-05",
            contents=prompt,
            config={
                "system_instruction": SYSTEM_INSTRUCTION,
                "response_mime_type": "application/json",
                "temperature": 0.2
            }
        )
       
        # Čišćenje odgovora od eventualnih markdown tagova
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
       
        return json.loads(raw_text)
       
    except Exception as e:
        print(f"AI Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-lead")
async def save_lead(data: dict):
    # Slanje izveštaja na mejl koristeći ispravno ime funkcije
    send_elite_report(
        data.get('email'),
        data.get('premium_content'),
        data.get('score'),
        data.get('competitor_name')
    )
    return {"status": "success"}

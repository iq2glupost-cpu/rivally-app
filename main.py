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

# --- CORE CONFIG ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASSWORD") # USKLAĐENO SA VERCELOM
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

# INICIJALIZACIJA BAZE
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

if GEMINI_API_KEY: genai.configure(api_key=GEMINI_API_KEY)

# --- THE ELITE MASTER TEMPLATE --- (TVOJ DIZAJN NETAKNUT)
def send_master_report(target_email, premium_content, score, competitor):
    if not SMTP_USER or not SMTP_PASS:
        print("SMTP Greška: Nedostaju SMTP_USER ili SMTP_PASSWORD na Vercelu")
        return
  
    msg = MIMEMultipart()
    msg["Subject"] = f"CLASSIFIED: Strategic Intelligence Briefing | Dominance: {score}%"
    msg["From"] = f"SAKORP CORPORATION <{SMTP_USER}>"
    msg["To"] = target_email
  
    # Tvoj originalni HTML stil
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
                                <div style="font-family: 'Playfair Display', serif; font-size: 28px; font-weight: bold;">SAKORP <span style="color: #2563eb;">CORPORATION</span></div>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 50px;">
                                <div style="text-align: center; margin-bottom: 50px;">
                                    <div style="font-size: 110px; font-weight: 900; color: #000;">{score}%</div>
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
            print("Mejl uspešno poslat.")
    except Exception as e:
        print(f"SMTP Greška: {e}")

# --- AI INSTRUCTIONS --- (TVOJE INSTRUKCIJE)
SYSTEM_INSTRUCTION = """
You are RIVALLY - SAKORP's chief intelligence officer. Output VALID JSON.
TONE: Institutional, precise, brutal.
FIELDS: dominance_score, score_explanation, tactical_breach, premium_report
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-pro", 
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config={"response_mime_type": "application/json", "temperature": 0.2}
)

@app.get("/", response_class=HTMLResponse)
async def read_index(): return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(data: dict):
    # Pristup podacima usklađen sa tvojim front-endom
    my_name = data['my_product']['name']
    comp_name = data['competitor_product']['name']
    prompt = f"Battle: {my_name} vs {comp_name}."
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text.strip())
    except: raise HTTPException(status_code=500)

@app.post("/save-lead")
async def save_lead(data: dict):
    # Supabase log (Proveri da li tabela 'history' postoji)
    if supabase:
        try:
            supabase.table("history").insert({
                "business_name": data.get('product_name', 'Unknown'),
                "email": data['email']
            }).execute()
        except Exception as e: print(f"Supabase Greška: {e}")

    # Slanje mejla (Usklađeno sa tvojom funkcijom)
    send_master_report(
        data['email'],
        data.get('premium_content', 'Analiza u Master File-u.'),
        data.get('score', 0),
        data.get('competitor_name', 'Rival')
    )
    return {"status": "success"}


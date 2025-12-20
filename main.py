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

# --- KONFIGURACIJA ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")

# --- FUNKCIJA ZA SLANJE MEJLA ---
def send_elite_report(target_email, premium_content, score, competitor):
    if not SMTP_USER or not SMTP_PASS: return
    clean_email = target_email.strip().lower()
    msg = MIMEMultipart()
    msg["Subject"] = f"CLASSIFIED: Strategic Intelligence Briefing | Dominance: {score}%"
    msg["From"] = f"SAKORP CORPORATION <{SMTP_USER}>"
    msg["To"] = clean_email
   
    # HTML prilagođen brendu
    body = f"""
    <html><body style="background:#000;color:#fff;padding:40px;font-family:Arial;">
    <h1 style="color:#2563eb;">SAKORP INTELLIGENCE</h1>
    <p>Strategic audit vs {competitor} complete.</p>
    <div style="font-size:40px;margin:20px 0;">Score: {score}%</div>
    <hr style="border-color:#2563eb;">
    <div style="color:#ccc;line-height:1.6;">{premium_content}</div>
    </body></html>
    """
    msg.attach(MIMEText(body, "html"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except: pass

@app.get("/", response_class=HTMLResponse)
async def read_index(): return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(data: dict):
    # Koristimo tvoj API ključ i najnoviji brzi model
    client = genai.Client(api_key=GEMINI_API_KEY)
   
    my_p = data.get('my_product', {})
    comp_p = data.get('competitor_product', {})
   
    prompt = f"Battle: {my_p.get('name')} vs {comp_p.get('name')}. Audience: {data.get('target_audience')}."
   
    # Instrukcija koja osigurava da podaci odgovaraju tvom index.html fajlu
    system_instruction = """
    You are RIVALLY officer. Output VALID JSON.
    FIELDS: dominance_score (int), score_explanation (str), tactical_breach (str), premium_report (HTML str).
    """

    try:
        # AKTIVIRAMO GEMINI-3-FLASH ZA MAKSIMALNU BRZINU
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "temperature": 0.2
            }
        )
       
        # Sigurno čišćenje JSON odgovora
        res_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(res_text)
       
    except Exception as e:
        print(f"AI Error: {e}")
        return {
            "dominance_score": 0,
            "score_explanation": "Neural Link Timeout. Refresh system.",
            "tactical_breach": "System recalibrating...",
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


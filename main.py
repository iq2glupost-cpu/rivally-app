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

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def send_elite_report(target_email, premium_content, score, competitor):
    if not SMTP_USER or not SMTP_PASS: return
    clean_email = target_email.strip().lower()
    msg = MIMEMultipart()
    msg["Subject"] = f"CLASSIFIED: Strategic Intelligence Briefing | Dominance: {score}%"
    msg["From"] = f"SAKORP CORPORATION <{SMTP_USER}>"
    msg["To"] = clean_email
    body = f"<html><body style='background:#000;color:#fff;padding:40px;'><h1>SAKORP Intelligence</h1><p>Score: {score}% vs {competitor}</p><hr>{premium_content}</body></html>"
    msg.attach(MIMEText(body, "html"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except Exception as e: print(f"Mail Error: {e}")

SYSTEM_INSTRUCTION = """You are RIVALLY officer. Output VALID JSON with: dominance_score (int), score_explanation (str), tactical_breach (str), premium_report (str)."""

@app.get("/", response_class=HTMLResponse)
async def read_index(): return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(data: dict):
    my_p = data.get('my_product', {})
    comp_p = data.get('competitor_product', {})
    prompt = f"Analyze: {my_p.get('name')} vs {comp_p.get('name')}. Audience: {data.get('target_audience')}."
    try:
        response = client.models.generate_content(
            model="gemini-2.0-pro-exp-02-05",
            contents=prompt,
            config={"system_instruction": SYSTEM_INSTRUCTION, "response_mime_type": "application/json", "temperature": 0.2}
        )
        return json.loads(response.text.replace('```json', '').replace('```', '').strip())
    except: raise HTTPException(status_code=500)

@app.post("/save-lead")
async def save_lead(data: dict):
    # Ova ruta prima podatke sa sajta i šalje mejl
    send_elite_report(
        data.get('email'),
        data.get('premium_content'),
        data.get('score'),
        data.get('competitor_name')
    )
    return {"status": "success"}

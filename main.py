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

# CONFIG
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None
if GEMINI_API_KEY: genai.configure(api_key=GEMINI_API_KEY)

# INSTRUKCIJE ZA DUBOKI IZVEŠTAJ
SYSTEM_INSTRUCTION = """
You are RIVALLY - An elite competitive marketing strategist.
Output ONLY valid JSON with fields: 'dominance_score', 'score_explanation' (provocative teaser), and 'html_content' (long, deep-dive tactical audit).
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-pro",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config={"response_mime_type": "application/json"}
)

def send_strategic_email(target_email, report_content, score, competitor):
    if not SMTP_USER: return
    msg = MIMEMultipart()
    msg["Subject"] = f"RIVALLY STRATEGIC AUDIT: {score}% Dominance vs {competitor}"
    msg["From"] = f"SAKORP RIVALLY <{SMTP_USER}>"
    msg["To"] = target_email
    body = f"""<div style="background:#000; color:#fff; padding:30px; font-family:sans-serif;">
        <h1 style="color:#2563eb;">Strategic Report complete.</h1>
        <h2 style="font-size:40px;">Your Dominance Score: {score}%</h2>
        <hr style="border-color:#333;">
        <div style="color:#ccc;">{report_content}</div>
        <p style="margin-top:30px; font-size:10px; color:#555;">SAKORP HOLDING // AI DIVISION</p>
    </div>"""
    msg.attach(MIMEText(body, "html"))
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except Exception as e: print(f"Email Error: {e}")

@app.get("/", response_class=HTMLResponse)
async def read_index(): return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(data: dict):
    prompt = f"Battle: {data['my_product']} vs {data['competitor_product']}. Strategic scan for dominance."
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
    # AKTIVIRANJE MEJLA
    send_strategic_email(data['email'], data['report_html'], data['score'], data['competitor_name'])
    return {"status": "success"}

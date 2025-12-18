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
from typing import Any, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ENV
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")

supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except: pass

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class ComparisonRequest(BaseModel):
    my_product: Any
    competitor_product: Any
    target_audience: str
   
class LeadRequest(BaseModel):
    email: str
    score: int
    product_name: str
    competitor_name: str
    report_html: str

model = genai.GenerativeModel(
    model_name="gemini-2.5-pro",
    generation_config={"response_mime_type": "application/json"}
)

def send_strategic_email(target_email, report_content, score, competitor):
    if not SMTP_USER: return
    msg = MIMEMultipart()
    msg["Subject"] = f"RIVALLY REPORT: Score {score}/100 vs {competitor}"
    msg["From"] = f"SAKORP RIVALLY <{SMTP_USER}>"
    msg["To"] = target_email
    body = f"<div style='background:#000; color:#fff; padding:30px;'><h1>Audit Score: {score}/100</h1><hr>{report_content}</div>"
    msg.attach(MIMEText(body, "html"))
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except: pass

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(request: ComparisonRequest):
    prompt = f"Analyze competition battle between {request.my_product} and {request.competitor_product}. Return JSON."
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except: raise HTTPException(status_code=500)

@app.post("/save-lead")
async def save_lead(request: LeadRequest):
    if supabase:
        try:
            supabase.table("history").insert({"business_name": request.product_name, "email": request.email}).execute()
        except: pass
    send_strategic_email(request.email, request.report_html, request.score, request.competitor_name)
    return {"status": "success"}

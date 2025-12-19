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

# --- CORS KONFIGURACIJA ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENVIRONMENT VARIABLES (Vercel Settings) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# SMTP PODACI ZA SLANJE MEJLOVA
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER") # Tvoj email
SMTP_PASS = os.environ.get("SMTP_PASS") # App Password

# --- INICIJALIZACIJA EKSTERNIH SERVISA ---
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase konekcija aktivna.")
    except Exception as e:
        print(f"⚠️ Supabase Error: {e}")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- MODELI PODATAKA ---
class ProductData(BaseModel):
    name: str
    url: Optional[str] = None
    features: Any
    price: Optional[str] = "N/A"

class ComparisonRequest(BaseModel):
    my_product: ProductData
    competitor_product: ProductData
    target_audience: str
   
class LeadRequest(BaseModel):
    email: str
    score: int
    product_name: str
    competitor_name: str
    report_html: str

# --- AI PODEŠAVANJA (TEASER & HOOK LOGIKA) ---
# Instrukcija kaže AI-u da razdvoji kratku "udarnu" rečenicu od punog izveštaja
SYSTEM_INSTRUCTION = """
You are RIVALLY - An elite competitive marketing strategist.
YOUR OUTPUT MUST BE ONLY VALID JSON.

JSON STRUCTURE:
1. "dominance_score" (Integer 0-100): Probability of winning.
2. "score_explanation" (String): A PUNCHY, PROVOCATIVE summary (TEASER) that highlights a critical gap. This is visible immediately to the user.
3. "reality_check" (Object): { "competitor_wins": [], "improvements_needed": [] }
4. "html_content" (String): The COMPLETE, DETAILED tactical report (HTML format). This will be blurred initially.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-pro",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config=genai.GenerationConfig(response_mime_type="application/json")
)

# --- FUNKCIJA ZA AUTOMATSKO SLANJE MEJLA ---
def send_strategic_email(target_email, report_content, score, competitor):
    if not SMTP_USER or not SMTP_PASS:
        print("⚠️ Mejl nije poslat: SMTP podaci nisu podešeni u Vercelu.")
        return
   
    msg = MIMEMultipart()
    msg["Subject"] = f"RIVALLY REPORT: Score {score}/100 vs {competitor}"
    msg["From"] = f"SAKORP RIVALLY <{SMTP_USER}>"
    msg["To"] = target_email

    # Dizajn izveštaja koji stiže u inbox
    body = f"""
    <div style="background:#000; color:#fff; padding:40px; font-family:sans-serif;">
        <h2 style="color:#2563eb; letter-spacing:2px; font-size:12px;">STRATEGIC AUDIT</h2>
        <h1 style="font-size:48px; margin:10px 0;">{score}/100</h1>
        <hr style="border:0; border-top:1px solid #333; margin:20px 0;">
        <div style="color:#ccc; line-height:1.6;">{report_content}</div>
        <p style="margin-top:40px; font-size:10px; color:#444;">CONFIDENTIAL // SAKORP HOLDING SYSTEMS &copy; 2025</p>
    </div>
    """
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            print(f"✅ Izveštaj uspešno poslat na {target_email}")
    except Exception as e:
        print(f"⚠️ Greška pri slanju mejla: {e}")

# --- ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(request: ComparisonRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Nedostaje API ključ.")

    prompt = f"""
    ANALYZE:
    ME: {request.my_product.url}, Features: {request.my_product.features}
    RIVAL: {request.competitor_product.url}, Features: {request.competitor_product.features}
    AUDIENCE: {request.target_audience}
    """

    try:
        response = model.generate_content(prompt)
        ai_data = json.loads(response.text)

        # Čuvanje analize u istoriju (Supabase)
        if supabase:
            try:
                supabase.table("history").insert({
                    "business_name": request.my_product.url,
                    "ai_response": response.text
                }).execute()
            except: pass

        return ai_data
    except Exception as e:
        print(f"AI Error: {e}")
        raise HTTPException(status_code=500, detail="Greška u AI analizi.")

@app.post("/save-lead")
async def save_lead(request: LeadRequest):
    # 1. Čuvanje mejla u bazu za prodaju
    if supabase:
        try:
            supabase.table("history").insert({
                "business_name": request.product_name,
                "email": request.email,               
                "ai_response": f"Captured lead for {request.competitor_name}"              
            }).execute()
        except: pass

    # 2. Slanje kompletnog izveštaja na mejl korisnika
    send_strategic_email(request.email, request.report_html, request.score, request.competitor_name)
   
    return {"status": "success"}

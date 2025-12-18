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

# Omogućavanje CORS-a kako bi frontend mogao nesmetano da komunicira sa backendom
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- KONFIGURACIJA (Preuzima se iz Vercel Environment Variables) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# SMTP PODACI ZA SLANJE MEJLOVA
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER")  # Vaš email (npr. office@sakorp.com)
SMTP_PASS = os.environ.get("SMTP_PASS")  # App Password za email

# Inicijalizacija Supabase klijenta
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase povezan.")
    except Exception as e:
        print(f"⚠️ Supabase greška: {e}")

# Inicijalizacija Gemini AI
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- MODELI PODATAKA ---
class ProductData(BaseModel):
    name: str
    price: str
    features: Any
    weaknesses: Optional[str] = None
    url: Optional[str] = None

class ComparisonRequest(BaseModel):
    my_product: ProductData
    competitor_product: ProductData
    target_audience: str
   
class LeadRequest(BaseModel):
    email: str
    score: int
    product_name: str
    competitor_name: str
    report_html: Optional[str] = ""

# --- AI KONFIGURACIJA ---
SYSTEM_INSTRUCTION = """
You are RIVALLY - An elite competitive marketing strategist by SAKORP.
Your goal is to help the user dominate their market.
Generate a JSON response with:
1. "dominance_score" (0-100)
2. "score_explanation" (String)
3. "reality_check" (Object: competitor_wins, improvements_needed)
4. "fatherly_advice" (String)
5. "html_content" (String with <h3>, <p>, <ul>)
6. "instagram_caption" (String)
ONLY return valid JSON.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-pro",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json"
    )
)

# --- POMOĆNA FUNKCIJA ZA SLANJE MEJLA ---
def send_strategic_email(target_email, report_content, score, competitor):
    if not SMTP_USER or not SMTP_PASS:
        print("⚠️ Email Warning: SMTP_USER ili SMTP_PASS nisu podešeni.")
        return False
   
    msg = MIMEMultipart()
    msg["Subject"] = f"RIVALLY AUDIT: {score}/100 Dominance vs {competitor}"
    msg["From"] = f"SAKORP RIVALLY <{SMTP_USER}>"
    msg["To"] = target_email

    # Kreiranje HTML tela mejla
    email_body = f"""
    <div style="font-family: sans-serif; background-color: #000; color: #fff; padding: 40px;">
        <h1 style="color: #2563eb;">Strategic Intelligence Report</h1>
        <p>Your Dominance Score against <strong>{competitor}</strong> is:</p>
        <div style="font-size: 48px; font-weight: bold; color: #2563eb;">{score}/100</div>
        <hr style="border: 0; border-top: 1px solid #333; margin: 20px 0;">
        <div style="color: #ccc;">{report_content}</div>
        <p style="font-size: 10px; color: #444; margin-top: 40px;">CONFIDENTIAL // SAKORP HOLDING SYSTEM</p>
    </div>
    """
    msg.attach(MIMEText(email_body, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            print(f"✅ Email uspešno poslat na {target_email}")
            return True
    except Exception as e:
        print(f"⚠️ SMTP Error: {e}")
        return False

# --- ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(request: ComparisonRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Nedostaje API Key.")

    my_features = str(request.my_product.features)
    comp_features = str(request.competitor_product.features)
    comp_url_text = f", URL: {request.competitor_product.url}" if request.competitor_product.url else ""

    prompt = f"""
    ANALYZE:
    ME: {request.my_product.name}, {request.my_product.price}, {my_features}, Weakness: {request.my_product.weaknesses}
    RIVAL: {request.competitor_product.name}, {request.competitor_product.price}, {comp_features}{comp_url_text}
    AUDIENCE: {request.target_audience}
    """

    try:
        response = model.generate_content(prompt)
        ai_output_text = response.text.strip()
        parsed_json = json.loads(ai_output_text)

        # Čuvanje u Supabase bazu
        if supabase:
            try:
                supabase.table("history").insert({
                    "business_name": request.my_product.name,
                    "ai_response": ai_output_text
                }).execute()
            except Exception as db_e:
                print(f"⚠️ DB Error: {db_e}")

        return parsed_json
    except Exception as e:
        print(f"AI Error: {e}")
        raise HTTPException(status_code=500, detail="Greška u AI analizi.")

@app.post("/save-lead")
async def save_lead(request: LeadRequest):
    # 1. Čuvanje lead-a u bazu
    if supabase:
        try:
            supabase.table("history").insert({
                "business_name": request.product_name,
                "email": request.email,               
                "ai_response": f"Email unlocked report for competitor: {request.competitor_name}"              
            }).execute()
        except Exception as e:
            print(f"DB Lead Error: {e}")
   
    # 2. Slanje rezultata na mejl korisnika
    send_strategic_email(
        target_email=request.email,
        report_content=request.report_html,
        score=request.score,
        competitor=request.competitor_name
    )
   
    return {"status": "success", "message": "Lead saved and email sent."}

@app.get("/test-gemini")
def test_gemini():
    try:
        modeli = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return {"STATUS": "Uspesno povezan", "DOSTUPNI_MODELI": modeli}
    except Exception as e:
        return {"GRESKA": str(e)}

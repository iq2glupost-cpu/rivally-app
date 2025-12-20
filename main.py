import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from supabase import create_client

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- KONFIGURACIJA (Vercel Variables) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Inicijalizacija baze
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

# --- FUNKCIJA ZA MEJL ---
def send_elite_report(target_email, premium_content, score, competitor):
    if not SMTP_USER or not SMTP_PASS: return
    clean_email = target_email.strip().lower() # Rešava problem velikih slova
    msg = MIMEMultipart()
    msg["Subject"] = f"CLASSIFIED: Strategic Intelligence Briefing | Dominance: {score}%"
    msg["From"] = f"SAKORP CORPORATION <{SMTP_USER}>"
    msg["To"] = clean_email
   
    body = f"""
    <html><body style="background:#000;color:#fff;padding:40px;font-family:Arial;">
        <h1 style="color:#2563eb;">SAKORP <span style="color:#fff;">CORPORATION</span></h1>
        <hr style="border-color:#2563eb;">
        <div style="font-size:48px; font-weight:bold; margin:20px 0;">{score}%</div>
        <p>Market Dominance vs {competitor}</p>
        <div style="color:#ccc; line-height:1.6; background:#111; padding:20px; border-radius:10px;">
            {premium_content}
        </div>
    </body></html>
    """
    msg.attach(MIMEText(body, "html"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except Exception as e: print(f"Mail Error: {e}")

@app.get("/", response_class=HTMLResponse)
async def read_index(): return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(data: dict):
    client = genai.Client(api_key=GEMINI_API_KEY)
    my_p = data.get('my_product', {})
    comp_p = data.get('competitor_product', {})
    prompt = f"Analyze Battle: {my_p.get('name')} vs {comp_p.get('name')}. Audience: {data.get('target_audience')}."
   
    system_instruction = """You are RIVALLY officer. Output VALID JSON with: dominance_score (int), score_explanation (str), tactical_breach (str), premium_report (HTML str)."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config={"system_instruction": system_instruction, "response_mime_type": "application/json", "temperature": 0.2}
        )
        res_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(res_text)
    except: return {"dominance_score": 0, "score_explanation": "Link Error."}

@app.post("/save-lead")
async def save_lead(data: dict):
    email = data.get('email', '').strip().lower()
    premium_report = data.get('premium_content', '') # Ovo je odgovor koji baza traži
   
    # 1. UPIS U SUPABASE (Dodata kolona ai_response da baza ne bi izbacivala grešku)
    if supabase:
        try:
            supabase.table("history").insert({
                "business_name": data.get('product_name'),
                "email": email,
                "ai_response": premium_report  # OVO JE KLJUČNO ZA TVOJU BAZU
            }).execute()
        except Exception as e:
            print(f"Supabase Error: {e}")

    # 2. SLANJE MEJLA
    send_elite_report(
        email,
        premium_report,
        data.get('score', 0),
        data.get('competitor_name', 'Competitor')
    )
    return {"status": "success"}

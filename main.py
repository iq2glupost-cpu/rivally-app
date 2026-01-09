import os
import json
import re
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
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


def _clean_email(e: str) -> str:
    return (e or "").strip().lower()


def _is_valid_email(e: str) -> bool:
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$", _clean_email(e)))


def _extract_json(text: str) -> dict:
    """
    Robust JSON extraction:
    - removes ```json fences
    - tries json.loads on entire text
    - fallback: find first {...} block and parse it
    """
    if not text:
        raise ValueError("Empty model response")

    cleaned = text.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    # Try direct parse
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Fallback: find first JSON object
    m = re.search(r"\{[\s\S]*\}", cleaned)
    if not m:
        raise ValueError("No JSON object found in response")

    return json.loads(m.group(0))


# --- FUNKCIJA ZA MEJL ---
def send_elite_report(target_email, premium_content, score, competitor):
    if not SMTP_USER or not SMTP_PASS:
        return

    clean_email = _clean_email(target_email)
    if not _is_valid_email(clean_email):
        return

    msg = MIMEMultipart()
    msg["Subject"] = f"CLASSIFIED: Strategic Intelligence Briefing | Dominance: {score}%"
    msg["From"] = f"SAKORP CORPORATION <{SMTP_USER}>"
    msg["To"] = clean_email

    # basic hardening: ensure it's a string
    premium_content = premium_content or ""
    competitor = competitor or "Competitor"

    body = f"""
    <html>
      <body style="background:#000;color:#fff;padding:40px;font-family:Arial;">
        <h1 style="color:#2563eb;">SAKORP <span style="color:#fff;">CORPORATION</span></h1>
        <hr style="border-color:#2563eb;">
        <div style="font-size:48px; font-weight:bold; margin:20px 0;">{score}%</div>
        <p style="color:#bbb;">Market Dominance vs <b style="color:#fff;">{competitor}</b></p>
        <div style="color:#ccc; line-height:1.7; background:#111; padding:20px; border-radius:12px; border:1px solid #1f1f1f;">
          {premium_content}
        </div>
        <p style="margin-top:18px;color:#555;font-size:12px;">
          Confidential briefing — intended for recipient only.
        </p>
      </body>
    </html>
    """
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except Exception as e:
        print(f"Mail Error: {e}")


@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse('index.html')


@app.post("/generate-rival-strategy")
async def generate_strategy(data: dict):
    if not GEMINI_API_KEY:
        return {"dominance_score": 0, "score_explanation": "AI key missing.", "tactical_breach": "N/A", "premium_report": ""}

    client = genai.Client(api_key=GEMINI_API_KEY)

    my_p = data.get('my_product', {}) or {}
    comp_p = data.get('competitor_product', {}) or {}

    market_category = (data.get('market_category') or '').strip()
    primary_goal = (data.get('primary_goal') or '').strip()
    audience = (data.get('target_audience') or '').strip()

    # ✅ Better prompt (uses new fields)
    prompt = f"""
Analyze a competitive battle.

SUBJECT (Alpha):
- Name: {my_p.get('name')}
- URL: {my_p.get('url')}
- Price: {my_p.get('price')}
- Features: {my_p.get('features')}

TARGET (Beta):
- Name: {comp_p.get('name')}
- URL: {comp_p.get('url')}
- Price: {comp_p.get('price')}
- Notes/Vulnerabilities: {comp_p.get('features')}

Context:
- Market/Category: {market_category or "Unknown"}
- Audience: {audience or "Unknown"}
- Primary Goal: {primary_goal or "Win positioning + growth"}

Return a harsh, operator-grade assessment with clear actions.
""".strip()

    system_instruction = """You are a RIVALLY intelligence officer.
Return VALID JSON ONLY with these keys:
- dominance_score (int 0-100)
- score_explanation (string, concise but punchy)
- tactical_breach (string, one strong vulnerability or attack angle)
- premium_report (string HTML, structured with headings + bullet lists, actionable)

Rules:
- Output MUST be valid JSON.
- premium_report MUST be safe HTML (no scripts).
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "temperature": 0.2
            }
        )

        parsed = _extract_json(response.text)

        # normalize output
        dominance = parsed.get("dominance_score", 0)
        try:
            dominance = int(dominance)
        except Exception:
            dominance = 0
        dominance = max(0, min(100, dominance))

        return {
            "dominance_score": dominance,
            "score_explanation": parsed.get("score_explanation", "Signal unstable."),
            "tactical_breach": parsed.get("tactical_breach", "No breach identified."),
            "premium_report": parsed.get("premium_report", "")
        }

    except Exception as e:
        print("AI Error:", e)
        return {"dominance_score": 0, "score_explanation": "Link Error.", "tactical_breach": "N/A", "premium_report": ""}


@app.post("/save-lead")
async def save_lead(data: dict):
    email = _clean_email(data.get('email', ''))
    if not _is_valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email")

    premium_report = data.get('premium_content', '') or ""

    # 1. UPIS U SUPABASE
    if supabase:
        try:
            supabase.table("history").insert({
                "business_name": data.get('product_name'),
                "email": email,
                "ai_response": premium_report # ✅ your DB expects this
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

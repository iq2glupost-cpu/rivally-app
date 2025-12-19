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

# --- CONFIGURATION (Ensure these are in Vercel) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None
if GEMINI_API_KEY: genai.configure(api_key=GEMINI_API_KEY)

# --- MASTER EMAIL TEMPLATE FUNCTION ---
def send_master_report(target_email, premium_content, score, competitor):
    if not SMTP_USER: return
   
    msg = MIMEMultipart()
    msg["Subject"] = f"PRIORITY INTEL: {score}% Dominance Audit vs {competitor}"
    msg["From"] = f"SAKORP RIVALLY <{SMTP_USER}>"
    msg["To"] = target_email
   
    body = f"""
    <html>
    <body style="margin: 0; padding: 0; background-color: #000000; font-family: Arial, sans-serif; color: #ffffff;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #000000; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #050505; border: 1px solid #1e3a8a; border-radius: 4px; padding: 40px;">
                        <tr>
                            <td style="border-bottom: 1px solid #1e3a8a; padding-bottom: 20px;">
                                <div style="color: #2563eb; font-size: 10px; font-weight: bold; letter-spacing: 3px; text-transform: uppercase;">Confidential Intelligence Briefing</div>
                                <div style="color: #ffffff; font-size: 24px; font-weight: 900; font-style: italic; margin-top: 5px;">RIVALLY MASTER FILE</div>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="padding: 40px 0;">
                                <div style="font-size: 80px; font-weight: 900; color: #2563eb;">{score}%</div>
                                <div style="font-size: 10px; color: #555; text-transform: uppercase; letter-spacing: 4px;">Market Dominance Index</div>
                            </td>
                        </tr>
                        <tr>
                            <td style="color: #cccccc; font-size: 14px; line-height: 1.8;">{premium_content}</td>
                        </tr>
                        <tr>
                            <td style="padding-top: 30px;">
                                <div style="background-color: #0a0a0a; border: 1px dashed #1e3a8a; padding: 20px; text-align: center;">
                                    <div style="color: #2563eb; font-size: 12px; font-weight: bold;">STRATEGIC RECOMMENDATION:</div>
                                    <p style="font-size: 13px; color: #888;">Infrastructure gaps detected. SAKORP STUDIO can bridge these vulnerabilities.</p>
                                    <a href="https://sakorp.com/studio" style="display: inline-block; background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 12px 25px; font-size: 11px; font-weight: bold; text-transform: uppercase;">Contact Studio</a>
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
    except: pass

# --- AI INSTRUCTIONS ---
SYSTEM_INSTRUCTION = """
You are RIVALLY - SAKORP's strategic engine. Output VALID JSON ONLY.
FIELDS:
1. dominance_score (int)
2. score_explanation (teaser)
3. free_hook (one paragraph)
4. premium_report (Full HTML Master File with KILL-SHOT move, SWOT, 24-month forecast)
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
    prompt = f"Battle: {data['my_product']} vs {data['competitor_product']}. Target Audience: {data['target_audience']}."
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text.replace('```json', '').replace('```', '').strip())
    except: raise HTTPException(status_code=500)

@app.post("/save-lead")
async def save_lead(data: dict):
    # BELEŽENJE U BAZU (Supabase)
    if supabase:
        try:
            supabase.table("history").insert({
                "business_name": data['product_name'],
                "email": data['email']
            }).execute()
        except Exception as e: print(f"DB Error: {e}")
   
    # SLANJE MASTER IZVEŠTAJA NA MEJL
    send_master_report(data['email'], data['premium_content'], data['score'], data['competitor_name'])
    return {"status": "success"}

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
SMTP_USER = os.environ.get("SMTP_USER") # sakorp.rivally@gmail.com
SMTP_PASS = os.environ.get("SMTP_PASS") # 16-char App Password

if GEMINI_API_KEY: genai.configure(api_key=GEMINI_API_KEY)

# --- THE ELITE MASTER TEMPLATE ---
def send_elite_report(target_email, premium_content, score, competitor):
    if not SMTP_USER: return
   
    msg = MIMEMultipart()
    msg["Subject"] = f"CLASSIFIED: Strategic Intelligence Briefing | Dominance: {score}%"
    msg["From"] = f"SAKORP CORPORATION <{SMTP_USER}>"
    msg["To"] = target_email
   
    # HTML sa vodenim žigom i institucionalnim dizajnom
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
                       
                        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-30deg); font-size: 150px; color: rgba(37, 99, 235, 0.03); font-weight: 900; pointer-events: none; z-index: 0; white-space: nowrap;">
                            SAKORP
                        </div>

                        <tr>
                            <td style="padding: 40px; background-color: #000000; color: #ffffff;">
                                <table width="100%" border="0">
                                    <tr>
                                        <td>
                                            <div style="font-size: 10px; letter-spacing: 5px; text-transform: uppercase; color: #2563eb; font-weight: bold; margin-bottom: 5px;">Classified Strategic Asset</div>
                                            <div style="font-family: 'Playfair Display', serif; font-size: 28px; font-weight: bold; letter-spacing: -1px;">SAKORP <span style="color: #2563eb;">CORPORATION</span></div>
                                        </td>
                                        <td align="right" style="font-size: 10px; color: #666; font-family: monospace;">
                                            DOC_REF: INTEL-{score}-2025<br>STRICTLY CONFIDENTIAL
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding: 50px; position: relative; z-index: 1;">
                                <div style="text-align: center; margin-bottom: 50px;">
                                    <div style="font-size: 110px; font-weight: 900; color: #000; line-height: 1; letter-spacing: -5px;">{score}<span style="font-size: 40px; color: #2563eb;">%</span></div>
                                    <div style="font-size: 12px; font-weight: bold; color: #999; text-transform: uppercase; letter-spacing: 6px; margin-top: 10px;">Market Dominance Quotient</div>
                                </div>

                                <div style="border-left: 4px solid #2563eb; padding-left: 20px; margin-bottom: 40px;">
                                    <h3 style="font-family: 'Playfair Display', serif; font-size: 22px; color: #000; margin: 0 0 10px 0;">Executive Neural Audit</h3>
                                    <p style="color: #444; font-size: 15px; line-height: 1.6; margin: 0;">This document serves as a high-fidelity strategic audit between Target Alpha and Target Beta ({competitor}). No information within this briefing may be shared without SAKORP authorization.</p>
                                </div>

                                <div style="font-size: 15px; color: #333; line-height: 1.9; font-family: 'Inter', sans-serif;">
                                    {premium_content}
                                </div>

                                <table width="100%" border="0" style="margin-top: 50px; background-color: #fafafa; border: 1px solid #eeeeee; border-radius: 4px;">
                                    <tr>
                                        <td style="padding: 30px; text-align: center;">
                                            <div style="font-size: 11px; font-weight: bold; color: #2563eb; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 15px;">Strategic Countermeasure Recommended</div>
                                            <p style="color: #666; font-size: 14px; margin-bottom: 25px;">The identified market gaps require immediate architectural realignment. Deploy SAKORP division resources to neutralize threats.</p>
                                            <a href="https://sakorp.com/studio" style="background-color: #000000; color: #ffffff; padding: 16px 40px; text-decoration: none; font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; border-radius: 2px;">Contact SAKORP HQ</a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding: 30px 40px; background-color: #fafafa; border-top: 1px solid #eeeeee; text-align: center;">
                                <div style="font-size: 9px; color: #bbb; text-transform: uppercase; letter-spacing: 4px; font-weight: bold;">
                                    &copy; 2025 SAKORP HOLDING SYSTEMS // GLOBAL OPERATIONS UNIT
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
            server.starttls(); server.login(SMTP_USER, SMTP_PASS); server.send_message(msg)
    except: pass

# --- AI INSTRUCTIONS (Institutional Tone) ---
SYSTEM_INSTRUCTION = """
You are RIVALLY - SAKORP's chief intelligence officer. Output VALID JSON.
TONE: Institutional, precise, brutal. Use terms like 'Market Asymmetry', 'Capital Inefficiency', 'Tactical Leverage'.

FIELDS:
1. dominance_score (int)
2. score_explanation (Brief institutional teaser)
3. free_hook (One paragraph of deep market context)
4. premium_report (Full Master File in HTML. Sections: [I] NEURAL SWOT, [II] 24-MONTH COLLISION FORECAST, [III] STRATEGIC KILL-SHOT MOVE)
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


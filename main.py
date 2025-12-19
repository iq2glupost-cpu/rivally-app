import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
# NOVI IMPORT (menja stari google.generativeai)
from google import genai
from supabase import create_client

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- CORE CONFIG ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASSWORD")

# Inicijalizacija Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

# NOVA INICIJALIZACIJA KLIJENTA
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# --- [Ode ide tvoja funkcija send_elite_report - NE MENJA SE NIŠTA] ---

# --- AI INSTRUCTIONS ---
SYSTEM_INSTRUCTION = """
You are RIVALLY - SAKORP's chief intelligence officer. Output VALID JSON.
TONE: Institutional, precise, brutal. Use terms like 'Market Asymmetry', 'Capital Inefficiency', 'Tactical Leverage'.
... (ostatak tvoje instrukcije ostaje isti)
"""

@app.get("/", response_class=HTMLResponse)
async def read_index(): return FileResponse('index.html')

@app.post("/generate-rival-strategy")
async def generate_strategy(data: dict):
    prompt = f"Battle: {data['my_product']} vs {data['competitor_product']}. Target Audience: {data['target_audience']}."
    try:
        # NOVI NAČIN POZIVANJA MODELA (Podržava tvoj gemini-2.5-pro)
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config={
                "system_instruction": SYSTEM_INSTRUCTION,
                "response_mime_type": "application/json",
                "temperature": 0.2
            }
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"AI Error: {e}")
        raise HTTPException(status_code=500)

# --- [Ostatak koda save_lead ostaje ISTI] ---

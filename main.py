import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from supabase import create_client, Client

app = FastAPI()

# 1. CORS Setup

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Povezivanje Servisa
GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

SUPA_URL = os.environ.get("SUPABASE_URL")
SUPA_KEY = os.environ.get("SUPABASE_KEY")
supabase = None
if SUPA_URL and SUPA_KEY:
    try:
        supabase = create_client(SUPA_URL, SUPA_KEY)
    except:
        print("⚠️ Supabase nije povezan (proveri ključeve), ali sajt radi.")

# 3. Naslovna strana

@app.get("/")
async def read_index():
    return FileResponse('index.html')

# 4. MODEL PODATAKA (OVDE JE BILA GREŠKA 422) 🚨
# Sada prihvatamo običan tekst (str), ne rečnike (dict)!
class RivalryInput(BaseModel):
    my_product: str
    competitor: str
    target_audience: str

@app.post("/generate-rival-strategy")

async def generate_strategy(data: RivalryInput):
    try:
        # Prompt za Kevina O'Leary-ja
        prompt = f"""
        Act as a ruthless business strategist (Kevin O'Leary persona).
        Analyze this battle:
        ME (The Underdog): {data.my_product}
        THEM (The Giant): {data.competitor}
        TARGET AUDIENCE: {data.target_audience}

        Output specific, aggressive advice.
        Format exactly like this:
        Dominance Score: [Score/10]
        Winning Strategy: [3 bullet points]
        Fatherly Advice: [1 sentence]
        """

        if not GOOGLE_API_KEY:
            return {"winning_strategy": "Error: Server nema Gemini API Key."}

            
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        text_response = response.text

        # Cuvanje u bazu (Ovo sad radi jer je data.my_product običan string)
        if supabase:
            try:
                supabase.table("history").insert({

                    "business_name": data.my_product,  # Direktno upisujemo string
                    "ai_response": text_response
                }).execute()
                print("💾 Sačuvano u bazu!")
            except Exception as e:
                print(f"⚠️ Nije sačuvano u bazu: {e}")

        return {
            "dominance_score": "Analyzing...", 
            "winning_strategy": text_response,
            "fatherly_advice": "Go crush them." 
        }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

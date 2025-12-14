import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from supabase import create_client, Client

app = FastAPI()

# 1. CORS Podesavanja
app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Gemini Povezivanje
GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GOOGLE_API_KEY:
    print("❌ GRESKA: Nema GEMINI_API_KEY na Renderu!")
else:
    genai.configure(api_key=GOOGLE_API_KEY)


# 3. Supabase Povezivanje (SAFE MODE) 🛡️
SUPA_URL = os.environ.get("SUPABASE_URL")
SUPA_KEY = os.environ.get("SUPABASE_KEY")
supabase = None

try:
    if SUPA_URL and SUPA_KEY:
        supabase = create_client(SUPA_URL, SUPA_KEY)
        print("✅ Supabase povezan!")

    else:
        print("⚠️ UPOZORENJE: Nema Supabase kljuceva na Renderu. Baza nece raditi.")
except Exception as e:
    print(f"⚠️ Greska pri povezivanju na Supabase: {e}")

# Model podataka
class RivalryInput(BaseModel):
    my_product: dict
    competitor: dict
    target_audience: str@app.post("/generate-rival-strategy")
    async def generate_strategy(data: RivalryInput):
    try:
        # 1. Prompt
        prompt = f"""
        Act as a ruthless business strategist.
        Analyze:
        ME: {data.my_product}
        THEM: {data.competitor}
        AUDIENCE: {data.target_audience}

        Output format:
        Dominance Score: [Score/10]
        Winning Strategy: [3 bullet points]
        Fatherly Advice: [1 sentence]
        """

        # 2. Gemini Generisanje
        if not GOOGLE_API_KEY:
            return {"winning_strategy": "Error: Server nema Gemini API Key."}
            
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        text_response = response.text

        # 3. Parsiranje
        lines = text_response.split('\n')
        score = "7/10"
        for line in lines:
            if "Dominance Score:" in line:
                score = line.replace("Dominance Score:", "").strip()

        # 4. Cuvanje u Bazu (Samo ako baza radi)
        if supabase:
            try:
                user_business = data.my_product.get("name", "Unknown")
                supabase.table("history").insert({
                    "business_name": user_business,
                    "ai_response": text_response
                }).execute()
                print("💾 Sacuvano u bazu!")
            except Exception as e:

                print(f"⚠️ Nije sacuvano u bazu: {e}")

        return {
            "dominance_score": score,
            "winning_strategy": text_response,
            "fatherly_advice": "Go crush them." 
        }

    except Exception as e:
        print(f"General Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


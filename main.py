import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from supabase import create_client, Client

app = FastAPI()

# 1. Dozvoli pristup svima (CORS)
app.add_middleware(

    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Povezi se sa Google-om (Gemini)
# UZIMA KLJUC SA RENDERA (Sigurno!)
GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# 3. Povezi se sa Bazom (Supabase)
# UZIMA KLJUCEVE SA RENDERA
SUPA_URL = os.environ.get("SUPABASE_URL")
SUPA_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPA_URL, SUPA_KEY)

# Model podataka (sta primamo od korisnika)
class RivalryInput(BaseModel):
    my_product: dict

    competitor: dict
    target_audience: str@app.post("/generate-rival-strategy")
async def generate_strategy(data: RivalryInput):
    try:
        # 1. Pripremi Prompt za Gemini
        prompt = f"""
        Act as a ruthless business strategist like Kevin O'Leary.
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

        # 2. Pitaj Gemini
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        text_response = response.text

        # 3. Parsiranje odgovora (pretvaranje teksta u delove)
        # (Ovo je prosta logika, moze se poboljsati kasnije)
        lines = text_response.split('\n')
        score = "7/10" # Default

        strategy = text_response # Default
        
        for line in lines:
            if "Dominance Score:" in line:
                score = line.replace("Dominance Score:", "").strip()

        # ---------------------------------------------------------
        # 4. SACUVAJ U BAZU (SUPABASE) - OVO JE NOVO! 💾
        # ---------------------------------------------------------
        try:
            user_business = data.my_product.get("name", "Unknown Business")
            
            supabase.table("history").insert({
                "business_name": user_business,
                "ai_response": text_response
            }).execute()
            print("✅ Uspesno sacuvano u bazu!")

        except Exception as e:
            print(f"⚠️ Greska pri cuvanju u bazu (nije kriticno): {e}")

        # 5. Vrati odgovor sajtu
        return {
            "dominance_score": score,
            "winning_strategy": text_response,
            "fatherly_advice": "Go crush them." 
        }

    except Exception as e:
        print(f"Error: {e}")

        raise HTTPException(status_code=500, detail=str(e))

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
        pass

# 3. NOVO: Prikazi naslovnu stranu (index.html) 🖥️
@app.get("/")

async def read_index():
    return FileResponse('index.html')

# 4. Logika Aplikacije
class RivalryInput(BaseModel):
    my_product: dict
    competitor: dict
    target_audience: str

@app.post("/generate-rival-strategy")
async def generate_strategy(data: RivalryInput):
    try:

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


        if not GOOGLE_API_KEY:
            return {"winning_strategy": "Error: Server nema Gemini API Key."}
            
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        text_response = response.text

        # Cuvanje u bazu
        if supabase:

            try:
                user_business = data.my_product.get("name", "Unknown")
                supabase.table("history").insert({
                    "business_name": user_business,
                    "ai_response": text_response
                }).execute()
            except:
                pass

        return {
            "dominance_score": "Analyzing...", 
            "winning_strategy": text_response,
            "fatherly_advice": "Execute now." 
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from supabase import create_client, Client

app = FastAPI()

app.add_middleware(

    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/")
async def read_index():
    return FileResponse('index.html')


class RivalryInput(BaseModel):
    my_product: str
    competitor: str
    target_audience: str

@app.post("/generate-rival-strategy")
async def generate_strategy(data: RivalryInput):
    try:
        prompt = f"""
        Act as a ruthless business strategist. 
        ME: {data.my_product}

        THEM: {data.competitor}
        AUDIENCE: {data.target_audience}
        Provide: Dominance Score (0-10), 3 Bullet Points Strategy, 1 Sentence Advice.
        """

        text_response = "Error: AI not connected."
        if GOOGLE_API_KEY:
            # OVDE JE BILA GREŠKA - STAVILI SMO NOVI MODEL 👇
            model = genai.GenerativeModel("gemini-1.5-flash") 

            response = model.generate_content(prompt)
            text_response = response.text

        if supabase:
            try:
                supabase.table("history").insert({
                    "business_name": data.my_product,
                    "ai_response": text_response
                }).execute()
            except:
                pass


        return {
            "dominance_score": "Analyzing...",
            "winning_strategy": text_response,
            "fatherly_advice": "Execute."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

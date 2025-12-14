import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],

    allow_methods=["*"],
    allow_headers=["*"],
)

# SAMO GOOGLE KLJUC (Bazu smo izbacili)
GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

@app.get("/")
async def read_index():

    return FileResponse('index.html')

class InputData(BaseModel):
    my_product: str
    my_advantage: str
    competitor: str
    comp_weakness: str

@app.post("/generate")
async def generate(data: InputData):
    try:
        if not GOOGLE_API_KEY:
            return {"score": "0", "strategy": "Error: Nema API Ključa"}

        # Koristimo brzi Flash model
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        Compare these two:
        ME: {data.my_product} (Advantage: {data.my_advantage})
        THEM: {data.competitor} (Weakness: {data.comp_weakness})
        

        Analyze and return exactly in this format:
        SCORE: [Number 1-10]
        STRATEGY: [Detailed text]
        """
        
        response = model.generate_content(prompt)
        text = response.text
        
        # Izvlacenje ocene (prosta logika)
        import re
        score_match = re.search(r"SCORE:\s*(\d+)", text)
        score = score_match.group(1) if score_match else "7" # default ako ne nadje

        return {
            "score": score,
            "strategy": text.replace("SCORE:", "").replace(score, "").strip()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

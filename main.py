from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.responses import HTMLResponse
import os
import google.generativeai as genai
import json

# INICIJALIZACIJA (Korištenje FastAPI-a)
app = FastAPI()
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# KONAČAN MODEL KOJI SE KORISTI
MODEL_NAME = "gemini-2.5-pro"

# Pydantic model za prihvatanje podataka (sa opcionalnim URL-om)
class AnalysisRequest(BaseModel):
    companyName: str
    competitorName: str
    competitorUrl: str | None = None 

# RUTA ZA PRIKAZ HTML-a
@app.get("/", 

response_class=HTMLResponse)
async def home():
    try:
        # FastAPI/Vercel standard za prikaz index.html
        with open("index.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found!")

# RUTA ZA ANALIZU
@app.post("/api/analyze")
async def 

analyze_competition(request: AnalysisRequest):
    try:
        model = genai.GenerativeModel(MODEL_NAME)

        # Kreiranje Prompta
        url_context = (
            f"3. COMPETITOR WEBSITE: \"{request.competitorUrl}\" (Use this to identify their exact industry and strategic positioning)" 
            if request.competitorUrl else ""
        )
        
        prompt = f"""
        Act as a ruthless expert business strategist and competitive intelligence analyst. You MUST analyze the companies based on their business model and market strategy, not just their name.

        Compare these two companies:
        1. MY COMPANY: "{request.companyName}"

        2. COMPETITOR: "{request.competitorName}"
        {url_context}

        TASK:
        Analyze the strategic battle. Assume they compete in the same industry. Focus on concrete, actionable strategic moves and market gaps.
        
        Output strictly valid JSON only:
        {{
            "score": number (0-100, higher is better for My Company),

            "winner": "string",
            "summary": "string (A concise, 2-sentence executive summary of the situation)",
            "strengths": ["string", "string", "string"] (3 key advantages of My Company),
            "weaknesses": ["string", "string", "string"] (3 vulnerabilities of the Competitor we can exploit),
            "verdict": "string (A final, brutally honest advice, 1-2 sentences)"
        }}
        """


        response = model.generate_content(prompt)
        
        # Čišćenje JSON-a
        text_response = response.text
        if "```" in text_response:
            text_response = text_response.replace('```json', '').replace('```', '').strip()
        
        return json.loads(text_response)

    except Exception as e:

        print(f"Error during analysis: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed. AI could not process the request.")

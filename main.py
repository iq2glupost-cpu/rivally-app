from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.responses import HTMLResponse
import os
import google.generativeai as genai
import json

# INICIJALIZACIJA (Tvoja baza)
app = FastAPI()
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# KONAČAN MODEL KOJI SE KORISTI (NAJBRŽI PRO MODEL)
MODEL_NAME = "gemini-2.5-pro"

# Pydantic model za prihvatanje podataka (uključujući NOVO URL polje)
class AnalysisRequest(BaseModel):
    companyName: str
    competitorName: str
    competitorUrl: str | None = None # Novo opcionalno polje

# RUTA ZA PRIKAZ HTML-a

@app.get("/", response_class=HTMLResponse)
async def home():
    try:
        with open("index.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error: index.html not found!</h1>", 404

# RUTA ZA ANALIZU
@app.post("/api/analyze")
async def analyze_competition(request: AnalysisRequest):

    try:
        # Povezivanje na model
        model = genai.GenerativeModel(MODEL_NAME)

        # Kreiranje Prompta
        url_context = (
            f"3. COMPETITOR WEBSITE: \"{request.competitorUrl}\" (Use this to identify their exact industry)" 
            if request.competitorUrl else ""
        )

        
        prompt = f"""
        Act as a ruthless expert business strategist and competitive intelligence analyst. You MUST analyze the companies based on their business model and market strategy, not just their name.

        Compare these two companies:
        1. MY COMPANY: "{request.companyName}"
        2. COMPETITOR: "{request.competitorName}"

        {url_context}

        TASK:
        Analyze the strategic battle. If specific details are unknown, infer the business model from the names/website and assume they compete in the same industry. Focus on concrete strategic moves.
        
        Output strictly valid JSON only:
        {{
            "score": number (0-100, higher is better for My Company),

            "winner": "string",
            "summary": "string (A concise, 2-sentence executive summary of the situation)",
            "strengths": ["string", "string", "string"] (3 key advantages of My Company, e.g., 'Superior customer retention due to dedicated community support'),
            "weaknesses": ["string", "string", "string"] (3 vulnerabilities of the Competitor we can exploit, e.g., 'Weak pricing strategy leading to low profit margins'),
            "verdict": "string (A final, brutally honest advice, 1-2 sentences)"
        }}
        """

        response = model.generate_content(prompt)
        
        # Čišćenje JSON-a (važno za stabilnost)
        text_response = response.text
        if "```" in text_response:
            text_response = text_response.replace('```json', '').replace('```', '').strip()

        
        return json.loads(text_response)

    except Exception as e:
        print(f"Error during analysis: {e}")
        # Vraćamo grešku u slučaju problema sa AI
        raise HTTPException(status_code=500, detail="Analysis failed. AI could not process the request.")

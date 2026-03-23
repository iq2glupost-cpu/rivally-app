from flask import Flask, render_template, request, jsonify
from analiser import analyze_buybox
from supabase import create_client, Client
import os

# Povezivanje sa Supabase bazom
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/check", methods=["POST"])
def check():
    data = request.json
    asin = data.get("asin")
    seller_id = data.get("seller_id")

    # 🔥 IZMENJENO: seller_id više nije obavezan
    if not asin:
        return jsonify({
            "status": "error",
            "message": "ASIN is required."
        }), 400

    # Ako nije poslat ili je prazan → None
    if not seller_id:
        seller_id = None

    # 🔥 POZIV OSTAO ISTI
    result = analyze_buybox(asin, seller_id)

    return jsonify(result)

@app.route("/api/waitlist", methods=["POST"])
def waitlist():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({
            "status": "error",
            "message": "Email je obavezan."
        }), 400

    try:
        response = supabase.table('waitlist').insert({"email": email}).execute()
        return jsonify({
            "status": "success",
            "message": "Uspešno dodato na listu!"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True, port=5010)

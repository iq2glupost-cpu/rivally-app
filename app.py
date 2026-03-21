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
    # Prikazuje index.html korisniku
    return render_template("index.html")

@app.route("/api/check", methods=["POST"])
def check():
    # Prima podatke sa frontenda i šalje ih u analiser
    data = request.json
    asin = data.get("asin")
    seller_id = data.get("seller_id")

    if not asin or not seller_id:
        return jsonify({"status": "error", "message": "ASIN and Seller ID are required."}), 400

    result = analyze_buybox(asin, seller_id)
    return jsonify(result)

@app.route("/api/waitlist", methods=["POST"])
def waitlist():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"status": "error", "message": "Email je obavezan."}), 400

    try:
        # Ubacivanje emaila u tabelu 'waitlist'
        response = supabase.table('waitlist').insert({"email": email}).execute()
        return jsonify({"status": "success", "message": "Uspešno dodato na listu!"})
    except Exception as e:
        # Ako dođe do greške (npr. email već postoji)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    # Ovdje je promijenjen port na 5010
    app.run(debug=True, port=5010)

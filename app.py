from flask import Flask, render_template, request, jsonify
from analiser import analyze_buybox

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

if __name__ == "__main__":
    # Ovdje je promijenjen port na 5010
    app.run(debug=True, port=5010)


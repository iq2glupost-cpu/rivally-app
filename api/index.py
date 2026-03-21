from http.server import BaseHTTPRequestHandler
import urllib.parse
import json
import requests
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Čitamo parametre iz URL-a (ono što je sajt poslao)
        parsed_path = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_path.query)
        
        asin = query.get('asin', [''])[0]
        seller_id = query.get('seller_id', [''])[0]
        
        # Uzimamo tvoj Rainforest ključ iz Vercel-a
        api_key = os.environ.get('RAINFOREST_API_KEY')

        # Ako nema ASIN-a, vraćamo grešku odmah
        if not asin:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "ASIN is required"}).encode('utf-8'))
            return

        # 2. Spremamo upit za Rainforest API
        params = {
            'api_key': api_key,
            'type': 'product',
            'amazon_domain': 'amazon.com',
            'asin': asin,
            'output': 'json',
            'include_html': 'false' # Ovo drastično ubrzava Rainforest
        }

        try:
            # Šaljemo upit sa limitom od 9 sekundi da Vercel ne bi pukao prvi
            response = requests.get('https://api.rainforestapi.com/request', params=params, timeout=9)
            data = response.json()
            status = 200
        except requests.exceptions.Timeout:
            data = {"error": "Rainforest is taking too long."}
            status = 504
        except Exception as e:
            data = {"error": str(e)}
            status = 500

        # 3. Šaljemo podatke nazad tvom sajtu
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        self.wfile.write(json.dumps(data).encode('utf-8'))
        return


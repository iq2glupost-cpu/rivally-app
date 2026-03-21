from http.server import BaseHTTPRequestHandler
import json
import requests
import os # Ovo nam treba da "pročitamo" ključ sa Vercela

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Uzimamo ključ iz Vercel Environment Variables
        # (Na Vercelu ga nazovi RAINFOREST_KEY)
        api_key = os.environ.get('RAINFOREST_API_KEY')

        # Primer parametara za Rainforest (npr. tražimo određeni proizvod po ASIN-u)
        params = {
            'api_key': api_key,
            'type': 'product',
            'amazon_domain': 'amazon.com',
            'asin': 'B073JYC4XM' 
        }

        # Šaljemo zahtev Rainforest-u
        response = requests.get('https://api.rainforestapi.com/request', params=params)
        data = response.json()

        # Vraćamo odgovor tvom sajtu
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
        return


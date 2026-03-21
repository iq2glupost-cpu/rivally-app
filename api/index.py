from http.server import BaseHTTPRequestHandler
import urllib.parse
import json
import requests
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Priprema da uvek vratimo validan JSON nazad
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        parsed_path = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_path.query)
        
        asin = query.get('asin', [''])[0]
        api_key = os.environ.get('RAINFOREST_API_KEY')

        # PROVERA 1: Da li Vercel uopšte vidi ključ?
        if not api_key:
            self.wfile.write(json.dumps({"error": "Vercel ne vidi RAINFOREST_API_KEY. Proveri Environment Variables i uradi Redeploy."}).encode('utf-8'))
            return

        if not asin:
            self.wfile.write(json.dumps({"error": "ASIN nije poslat."}).encode('utf-8'))
            return

        params = {
            'api_key': api_key,
            'type': 'product',
            'amazon_domain': 'amazon.com',
            'asin': asin,
            'output': 'json',
            'include_html': 'false'
        }

        try:
            response = requests.get('https://api.rainforestapi.com/request', params=params, timeout=9)
            data = response.json()
            # Vraćamo sajtu TAČNO ono što je Rainforest odgovorio
            self.wfile.write(json.dumps(data).encode('utf-8'))
        except Exception as e:
            self.wfile.write(json.dumps({"error": f"Greška na serveru: {str(e)}"}).encode('utf-8'))
        return


from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Postavljamo statusni kod
        self.send_response(200)
        # Govorimo pregledaču da vraćamo JSON
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Tvoj odgovor
        odgovor = {
            "statusCode": 200,
            "body": "API radi"
        }
        
        # Šaljemo odgovor
        self.wfile.write(json.dumps(odgovor).encode('utf-8'))
        return


# my_server.py
from http.server import BaseHTTPRequestHandler, HTTPServer

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # HTTP 200 yanıtı gönder
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Hello, World! This is a Python HTTP server made by Alparslan.")

if __name__ == "__main__":
    # Sunucuyu 8080 portunda başlat
    server = HTTPServer(("0.0.0.0", 8080), SimpleHandler)
    print("Starting server on port 8080...")
    server.serve_forever()

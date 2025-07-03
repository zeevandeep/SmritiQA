"""
Simple Flask application that serves as a wrapper for our FastAPI app.

This script spawns a subprocess running uvicorn server which will
serve our FastAPI application. Flask app here acts just as a reverse proxy.
"""
import subprocess
import threading
import time
import sys
from flask import Flask, request, Response
import requests

# Create the Flask application
flask_app = Flask(__name__)

# Port for the uvicorn server
FASTAPI_PORT = 8000

# Variable to store the subprocess
uvicorn_process = None

def start_uvicorn():
    """Start uvicorn server as a subprocess."""
    global uvicorn_process
    if uvicorn_process is None:
        uvicorn_process = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn", 
                "app.main:app", 
                "--host", "127.0.0.1", 
                "--port", str(FASTAPI_PORT)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Give it time to start
        time.sleep(2)
        print(f"Started uvicorn on port {FASTAPI_PORT}")

@flask_app.before_request
def before_first_request():
    """Start uvicorn before handling the first request."""
    if uvicorn_process is None:
        start_uvicorn()

@flask_app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@flask_app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    """Proxy all requests to the FastAPI app."""
    # Forward request to FastAPI
    resp = requests.request(
        method=request.method,
        url=f"http://127.0.0.1:{FASTAPI_PORT}/{path}",
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
    )
    
    # Create Flask response from FastAPI response
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]
    
    response = Response(resp.content, resp.status_code, headers)
    return response

# Export the Flask app
app = flask_app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
    # Clean up uvicorn process when Flask exits
    if uvicorn_process:
        uvicorn_process.terminate()
        uvicorn_process.wait()
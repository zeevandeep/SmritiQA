"""
Script to start the FastAPI application directly.
"""
import subprocess
import sys
import time

def start_fastapi_server():
    """Start the FastAPI server directly using uvicorn."""
    print("Starting FastAPI server on port 8080...")
    
    # Start uvicorn in a subprocess
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8080"
    ]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Wait for server to start
    time.sleep(5)
    
    # Check if process is still running
    if process.poll() is None:
        print("FastAPI server started successfully.")
        return True
    else:
        print("Failed to start FastAPI server.")
        return False

if __name__ == "__main__":
    start_fastapi_server()
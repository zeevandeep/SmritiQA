"""
Main entry point for the unified Smriti FastAPI application.
"""
from asgi_adapter import WsgiAdapter
from app.main import app

# Create WSGI adapter for gunicorn compatibility
app = WsgiAdapter(app)

if __name__ == "__main__":
    import uvicorn
    from app.main import app as fastapi_app
    uvicorn.run(fastapi_app, host="0.0.0.0", port=5000)
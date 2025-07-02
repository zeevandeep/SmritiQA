"""
Server launcher for the Smriti application.

This script directly runs the application using Uvicorn.
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=5000, reload=True)
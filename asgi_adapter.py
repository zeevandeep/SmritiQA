"""
ASGI to WSGI adapter for the Smriti application.

This module provides a WSGI adapter for our FastAPI application to work with Gunicorn.
"""

import asyncio
import threading
from typing import Dict, List, Any
from urllib.parse import unquote


class WsgiAdapter:
    """WSGI adapter for ASGI applications."""
    
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app
        self._initialized = False
        
    def _ensure_initialization(self):
        """Ensure application is properly initialized."""
        if not self._initialized:
            try:
                # Initialize database
                from app.db.database import init_db
                init_db()
                
                # Initialize encryption
                from app.utils.encryption import init_encryption
                init_encryption()
                
                self._initialized = True
                print("WSGI adapter: Application initialized successfully")
                
            except Exception as e:
                print(f"WSGI adapter: Initialization failed: {e}")
                raise
        
    def __call__(self, environ, start_response):
        """WSGI entry point."""
        
        # Ensure initialization happens before first request
        self._ensure_initialization()
        
        # Create event loop for this request
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Storage for response data
        response_data = {
            'status': None,
            'headers': [],
            'body': b''
        }
        
        # Read request body
        content_length = int(environ.get('CONTENT_LENGTH', 0))
        if content_length > 0:
            body = environ['wsgi.input'].read(content_length)
        else:
            body = b''
        
        async def receive():
            """Mock receive function."""
            return {
                'type': 'http.request',
                'body': body,
                'more_body': False
            }
        
        async def send(message):
            """Mock send function."""
            if message['type'] == 'http.response.start':
                response_data['status'] = message['status']
                response_data['headers'] = message.get('headers', [])
            elif message['type'] == 'http.response.body':
                response_data['body'] += message.get('body', b'')
        
        async def call_asgi():
            """Call the ASGI application."""
            # Build headers from WSGI environ
            headers = []
            for key, value in environ.items():
                if key.startswith('HTTP_'):
                    # Convert HTTP_HEADER_NAME to header-name
                    header_name = key[5:].lower().replace('_', '-')
                    headers.append([header_name.encode(), value.encode()])
                elif key in ['CONTENT_TYPE', 'CONTENT_LENGTH']:
                    header_name = key.lower().replace('_', '-')
                    headers.append([header_name.encode(), value.encode()])
            
            scope = {
                'type': 'http',
                'method': environ.get('REQUEST_METHOD', 'GET'),
                'path': unquote(environ.get('PATH_INFO', '/')),
                'query_string': environ.get('QUERY_STRING', '').encode(),
                'headers': headers,
                'server': (environ.get('SERVER_NAME', 'localhost'), 
                          int(environ.get('SERVER_PORT', 80))),
                'scheme': environ.get('wsgi.url_scheme', 'http'),
            }
            
            await self.asgi_app(scope, receive, send)
        
        try:
            # Run the ASGI app
            loop.run_until_complete(call_asgi())
            
            # Start WSGI response
            status = response_data['status'] or 500
            status_text = status_code_to_text(status)
            headers = [(h[0].decode(), h[1].decode()) for h in response_data['headers']]
            start_response(f"{status} {status_text}", headers)
            
            return [response_data['body']]
            
        except Exception as e:
            # Error response
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
            return [f'Internal Server Error: {str(e)}'.encode()]


def status_code_to_text(status_code: int) -> str:
    """Convert HTTP status code to text."""
    status_texts = {
        200: 'OK',
        201: 'Created',
        302: 'Found',
        303: 'See Other',
        400: 'Bad Request',
        401: 'Unauthorized',
        403: 'Forbidden',
        404: 'Not Found',
        422: 'Unprocessable Entity',
        500: 'Internal Server Error'
    }
    return status_texts.get(status_code, 'Unknown')
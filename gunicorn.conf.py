"""
Gunicorn configuration optimized for audio transcription processing.
"""

# Server socket
bind = "0.0.0.0:5000"

# Worker processes
workers = 1
worker_class = "sync"

# Timeout settings for audio processing
timeout = 180  # 3 minutes for audio transcription
keepalive = 30

# Restart settings
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Performance
preload_app = True
worker_connections = 1000

# Development settings
reload = True
reuse_port = True
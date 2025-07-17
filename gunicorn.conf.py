"""
Gunicorn configuration optimized for audio transcription processing.
"""

# Server socket
bind = "0.0.0.0:5000"

# Worker processes
workers = 1
worker_class = "sync"

# Timeout settings for 5+ minute audio processing
timeout = 480  # 8 minutes for audio transcription (5 min audio + processing overhead)
keepalive = 60
graceful_timeout = 60

# Memory and restart settings
max_requests = 500  # Restart worker after 500 requests to prevent memory leaks
max_requests_jitter = 50
worker_tmp_dir = "/dev/shm"  # Use shared memory for better performance

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
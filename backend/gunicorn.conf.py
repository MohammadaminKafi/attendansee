"""
Gunicorn configuration file for AttendanSee backend.

This configuration is optimized for handling image processing tasks
that require longer processing times (face detection, embeddings, etc.)
"""

import multiprocessing
import os

# Bind to all interfaces on port 8000
bind = "0.0.0.0:8000"

# Worker configuration
# Use sync workers for CPU-intensive tasks like image processing
workers = int(os.getenv("GUNICORN_WORKERS", "4"))
worker_class = "sync"

# Timeout settings - increased for image processing
# 300 seconds (5 minutes) should be enough for most image processing tasks
timeout = int(os.getenv("GUNICORN_TIMEOUT", "300"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "300"))
keepalive = 5

# Max requests before worker restart (helps prevent memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# Request limits
limit_request_line = 0  # No limit on request line
limit_request_fields = 100
limit_request_field_size = 0  # No limit on header size

# Server mechanics
preload_app = False  # Don't preload to allow proper UV environment setup
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# Worker lifecycle hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Gunicorn server...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading workers...")

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    worker.log.info("Worker received INT or QUIT signal")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("Worker received SIGABRT signal")

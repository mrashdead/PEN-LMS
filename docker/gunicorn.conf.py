import os

bind = "0.0.0.0:8000"
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
threads = int(os.environ.get("GUNICORN_THREADS", "2"))
worker_class = "gthread"
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
graceful_timeout = 30
accesslog = "-"
errorlog = "-"
capture_output = True
forwarded_allow_ips = "*"
max_requests = 1000
max_requests_jitter = 100

import sys
import os

# Add backend root to sys.path for Vercel Serverless Function imports
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app

# Vercel Python runtime exports app entrypoint
__all__ = ["app"]

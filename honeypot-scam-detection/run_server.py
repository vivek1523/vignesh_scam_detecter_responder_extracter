"""
Run script for Honeypot API using Waitress server (production-ready)
Use this instead of gunicorn on Windows
"""

from waitress import serve
from app import app
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    threads = 4
    
    print("=" * 60)
    print("🎣 Honeypot Scam Detection API - Starting...")
    print("=" * 60)
    print(f"Server: Waitress (production-ready)")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Threads: {threads}")
    print(f"URL: http://localhost:{port}")
    print("=" * 60)
    print("Press CTRL+C to quit")
    print("=" * 60)
    print()
    
    serve(
        app,
        host=host,
        port=port,
        threads=threads,
        connection_limit=1000,
        channel_timeout=120
    )

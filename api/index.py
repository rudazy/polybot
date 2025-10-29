"""
Vercel Serverless Function Entry Point
"""
import sys
import os

# Add parent directory to path to import modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import the FastAPI app
from api_server import app
from mangum import Mangum

# Mangum handler for Vercel
handler = Mangum(app, lifespan="off")

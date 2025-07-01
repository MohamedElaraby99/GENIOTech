#!/usr/bin/env python3
"""
WSGI Entry Point for Production Deployment
"""

import os
import sys
from dotenv import load_dotenv

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables from .env file if it exists
if os.path.exists('.env'):
    load_dotenv('.env')

# Set default environment
os.environ.setdefault('FLASK_ENV', 'production')

from app import app
from config import config

# Configure the app for the current environment
config_name = os.environ.get('FLASK_ENV', 'production')
app.config.from_object(config[config_name])

# Application instance for WSGI server
application = app

if __name__ == "__main__":
    application.run() 
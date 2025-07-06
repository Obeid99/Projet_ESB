#!/usr/bin/env python3
"""
Database initialization script for ESB Chatbot (Docker-safe)
"""
import sys
import os
# Force DATABASE_URL to use localhost
os.environ["DATABASE_URL"] = "postgresql://esbuser:esbpass@localhost:5432/esbchatbot"
from dotenv import load_dotenv
load_dotenv(override=True)
from src.web.web_interface import app
from src.core.db_init import init_db
from src.core.models_db import db


def main():
    try:
        print("DATABASE_URL being used:", os.getenv("DATABASE_URL"))
        # Creating all database tables...
        init_db(app)
        # Database tables created!
    except:
        # Database initialization failed
        sys.exit(1)


if __name__ == "__main__":
    main()

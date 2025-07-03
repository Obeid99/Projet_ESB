#!/usr/bin/env python3
"""
Database initialization script for ESB Chatbot (Docker-safe)
"""
import sys
from src.web.web_interface import app
from src.core.db_init import init_db
from src.core.models_db import db


def main():
    try:
        # Creating all database tables...
        init_db(app)
        # Database tables created!
    except:
        # Database initialization failed
        sys.exit(1)


if __name__ == "__main__":
    main()

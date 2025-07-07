"""
Database initialization utility for ESB Chatbot (Flask-SQLAlchemy only)
"""
from .models_db import db, ensure_admin_user
 
 
def init_db(app):
    """
    Initialize the database tables using Flask app context.
    Usage:
        from src.core.db_init import init_db
        init_db(app)
    """
    with app.app_context():
        db.create_all()
        # Ensure admin user exists after table creation
        ensure_admin_user()
 
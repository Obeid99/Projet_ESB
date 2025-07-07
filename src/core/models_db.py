"""
SQLAlchemy models for user authentication, chat history, and project management
"""
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    # is_admin removed
    chats = db.relationship('ChatHistory', back_populates='user')
    projects = db.relationship('Project', backref='user')

# Utility to ensure a dummy admin user exists for admin chat history
def ensure_admin_user():
    """Ensure a dummy admin user exists in the database for admin chat history."""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin')
        )
        db.session.add(admin)
        db.session.commit()
    return admin.id

class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, nullable=False)  # True=user, False=bot
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    user = db.relationship('User', back_populates='chats')


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    # user relationship is handled by backref in User.projects

# Admin table for administration's session
# Removed Admin model, use hardcoded admin credentials instead

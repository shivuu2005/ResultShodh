from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Initialize database
db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    college_name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    profile_picture = db.Column(db.String(150), default='default.png')
    contact_number = db.Column(db.String(15), nullable=True)
    address = db.Column(db.String(255), nullable=True)

    def __init__(self, college_name, email, password, is_admin=False, profile_picture='default.png',
                 address=None, contact_number=None):
        self.college_name = college_name
        self.email = email
        self.password = password
        self.is_admin = is_admin
        self.profile_picture = profile_picture
        self.address = address
        self.contact_number = contact_number

    def __repr__(self):
        return f'<User {self.email}>'

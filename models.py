from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize database
db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    college_name = db.Column(db.String(255), nullable=True)  # Optional
    email = db.Column(db.String(255), unique=True, nullable=False)  # Required and unique
    password = db.Column(db.String(255), nullable=False)  # Hashed password
    is_admin = db.Column(db.Boolean, default=False)  # Default is false
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Automatically set creation time
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)  # Automatically set update time
    profile_picture = db.Column(db.String(150), default='default.png')  # Default profile picture
    contact_number = db.Column(db.String(15), nullable=True)  # Optional
    address = db.Column(db.String(255), nullable=True)  # Optional

    def __init__(self, college_name, email, password, is_admin=False, profile_picture='default.png',
                 address=None, contact_number=None):
        self.college_name = college_name
        self.email = email
        self.password = self.set_password(password)  # Store hashed password
        self.is_admin = is_admin
        self.profile_picture = profile_picture
        self.address = address
        self.contact_number = contact_number

    def set_password(self, password):
        """Hash the password for security."""
        return generate_password_hash(password)

    def check_password(self, password):
        """Check the hashed password against the provided password."""
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.email}>'

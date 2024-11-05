# config.py
import os

class Config:
    SECRET_KEY = 'Shivam2005'  # Secret key for sessions
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost/rgpv_bot_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable track modifications for performance reasons

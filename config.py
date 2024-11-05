# config.py
import os

class Config:
    SECRET_KEY = 'Shivam2005'  # Secret key for sessions
    SQLALCHEMY_DATABASE_URI = 'postgresql://rgpv_bot_db_user:Jea6fFA5qdnWLDL8cRbdMUHdlUZMQOsm@dpg-csl2usa3esus73fvles0-a/rgpv_bot_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable track modifications for performance reasons

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'scout-talent-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///scout_talent.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
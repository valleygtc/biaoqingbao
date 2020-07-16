import os

DEBUG = True if os.getenv('DEBUG') in ('True', 'true', '1') else False
# SQLALCHEMY_ECHO = True

TESTING = True if os.getenv('TESTING') in ('True', 'true', '1') else False

SQLALCHEMY_TRACK_MODIFICATIONS=False
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
assert SQLALCHEMY_DATABASE_URI

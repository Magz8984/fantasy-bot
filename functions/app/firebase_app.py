"""Firebase Admin initialization, kept separate so it only runs once
per cold start and can be imported safely from anywhere (routers,
services) without triggering re-initialization.
"""
import firebase_admin
from firebase_admin import db

from app.config import FIREBASE_DATABASE_URL

_initialized = False


def init_firebase():
    global _initialized
    if _initialized:
        return
    firebase_admin.initialize_app(options={
        "databaseURL": FIREBASE_DATABASE_URL,
    })
    _initialized = True


def get_ref(path: str):
    """Thin wrapper so services don't import firebase_admin.db directly."""
    return db.reference(path)

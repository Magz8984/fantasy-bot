"""
Centralized configuration. Pulls secrets/config from environment variables
rather than hardcoding them in source.

IMPORTANT: your original main.py had a live Anthropic API key hardcoded
as a string literal. That key is now exposed in your source history/repo.
You should:
  1. Rotate/revoke that key in the Anthropic console immediately.
  2. Set the new key via `firebase functions:secrets:set ANTHROPIC_API_KEY`
     (or, for local dev, an .env file loaded before this module imports).
"""
import os

FIREBASE_DATABASE_URL = os.environ.get(
    "FIREBASE_DATABASE_URL",
    "https://fantasy-f1-3a499-default-rtdb.firebaseio.com",
)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
SECRET_TOKEN = os.environ.get("SECRET_TOKEN", "a-secure-random-string-123")

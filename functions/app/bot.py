from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram import Update
from app.config import TELEGRAM_BOT_TOKEN, WEBHOOK_URL, SECRET_TOKEN

# FPL Oracle Bot token imported from environment variables

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Telegram bot imports
# Initialize Python-Telegram-Bot Application instance
ptb_app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# Track initialization state explicitly
_is_initialized = False


_is_initialized = False

async def ensure_initialized():
    global _is_initialized
    if not _is_initialized:
        await ptb_app.initialize()
        _is_initialized = True

# Define your bot handlers

async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responds to random text messages that are not commands."""
    user_text = update.message.text
    
    # Example: Simple echo response or friendly fallback message
    reply = f"I received your message: '{user_text}'. Send /start or /groupinfo to see available commands!"
    await update.message.reply_text(reply)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello from Cloud Functions and FastAPI!")


async def group_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        await update.message.reply_text(f"Group: {chat.title} (ID: {chat.id})")
    else:
        await update.message.reply_text("Run this inside a group!")

# Register handlers to PTB
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(CommandHandler("groupinfo", group_info))
ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_message))

logger.info(f"Module imported. WEBHOOK_URL value: {WEBHOOK_URL}")
# Handle lifecycle (setup webhook on startup, shutdown gracefully)

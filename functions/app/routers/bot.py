from app.config import SECRET_TOKEN, WEBHOOK_URL
from fastapi import APIRouter, Request, Response, status
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from telegram import Update
from app.bot import ptb_app, ensure_initialized

router = APIRouter(tags=["bot"], prefix="/bot")


@router.get("/setup-webhook")
async def setup_webhook():
    """Manual endpoint to register Telegram webhook on Firebase deployments."""
    if not WEBHOOK_URL:
        return {"ok": False, "error": "WEBHOOK_URL environment variable is missing"}

    # Safe initialization call
    await ensure_initialized()

    # Register the webhook URL with Telegram API
    success = await ptb_app.bot.set_webhook(
        url=f"{WEBHOOK_URL}/bot/webhook",
        secret_token=SECRET_TOKEN
    )

    return {
        "ok": success,
        "webhook_url": f"{WEBHOOK_URL}/bot/webhook"
    }


@router.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        # 1. Validate Secret Token
        header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if SECRET_TOKEN and header_secret != SECRET_TOKEN:
            return Response(status_code=status.HTTP_403_FORBIDDEN)

        # 2. Ensure initial setup
        await ensure_initialized()

        # 3. Parse update
        data = await request.json()
        update = Update.de_json(data, ptb_app.bot)

        # 4. Attempt processing with loop error recovery
        try:
            await ptb_app.process_update(update)
        except RuntimeError as loop_err:
            if "Event loop is closed" in str(loop_err):
                logger.warning("Event loop was closed by runtime. Re-initializing PTB Application...")
                await ptb_app.initialize()
                await ptb_app.process_update(update)
            else:
                raise loop_err

        return Response(status_code=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error handling update: {e}", exc_info=True)
        # Always return 200 OK so Telegram doesn't endlessly retry failing requests
        return Response(content="Internal error processed", status_code=status.HTTP_200_OK)
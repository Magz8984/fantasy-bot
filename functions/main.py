"""
Firebase Cloud Functions entry point.

This file should stay thin: it wires Firebase Functions to the FastAPI
app and nothing else. All route/business logic lives under app/.
"""
import asyncio
import json
import logging

from firebase_functions import https_fn
from firebase_functions.options import set_global_options

from app.firebase_app import init_firebase
from app.app_factory import create_app

logger = logging.getLogger(__name__)

# For cost control, cap the number of concurrent container instances.
# Per-function overrides are still possible via @https_fn.on_request(max_instances=...)
set_global_options(max_instances=10)

# Initialize Firebase Admin once per cold start.
init_firebase()

# Build the FastAPI app (routers mounted inside app_factory.create_app).
app = create_app()


@https_fn.on_request()
def main(req: https_fn.Request) -> https_fn.Response:
    """Bridges a Cloud Functions request into the ASGI FastAPI app."""
    try:
        asgi_request = {
            "type": "http",
            "method": req.method,
            "path": req.path,
            "headers": [
                (k.lower().encode(), v.encode()) for k, v in req.headers.items()
            ],
            "query_string": req.query_string or b"",
            "body": req.get_data() or b"",
        }

        async def receive():
            return {
                "type": "http.request",
                "body": req.get_data() or b"",
                "more_body": False,
            }

        response_body = []
        response_headers = []
        response_status = 200

        async def send(message):
            nonlocal response_body, response_headers, response_status
            if message["type"] == "http.response.start":
                response_status = message.get("status", 200)
                response_headers = message.get("headers", [])
            elif message["type"] == "http.response.body":
                response_body.append(message.get("body", b""))

        async def run_asgi():
            await app(asgi_request, receive, send)

        asyncio.run(run_asgi())

        full_body = b"".join(response_body)

        headers_dict = {
            (k.decode() if isinstance(k, bytes) else k): (
                v.decode() if isinstance(v, bytes) else v
            )
            for k, v in response_headers
        }

        return https_fn.Response(
            response=full_body,
            status=response_status,
            headers=headers_dict,
        )

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return https_fn.Response(
            response=json.dumps({"error": "Internal Server Error"}),
            status=500,
            headers={"Content-Type": "application/json"},
        )

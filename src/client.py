import asyncio
from typing import Callable

from src.settings import (
    # API_KEY,
    # PORT,
    # SERVER_IP,
    SERVER_URL,
    USE_SERVER,
)
from src import xplat

# if USE_SERVER and sys.platform not in ("emscripten", "wasm"):
#     import requests  # type: ignore[import-untyped]


BAD_API_KEY = "9"

PLAY_TOKEN = "321"
BAD_PLAY_TOKEN_1 = "9"
BAD_PLAY_TOKEN_2 = "zzz"

DUMMY_TELEMETRY_DATA = {"self_assessment": "ok"}

def authn(play_token: str, post_login_callback: Callable[[dict], None]) -> None:
    if USE_SERVER:
        url = f"{SERVER_URL}/authn"
        headers = {}
        payload = {
            "play_token": play_token,
        }
        # Do this all asynchronously:
        asyncio.create_task(
            xplat.post_request_with_callback(
                url,
                headers,
                payload,
                post_login_callback,
            )
        )
    else:
        post_login_callback({
            'token' : play_token,
            'jwt' : 'dummy_token',
            'game_version': 1,
        })

def send_telemetry(encoded_jwt: str, payload: dict) -> None:
    """Send telemetry to the backend, asynchronously."""
    # TODO: If needed, we can restructure this to do async callbacks
    # as well, in case we need to react to this telemetry being sent.
    xplat.log(f"Sending telemetry: {payload}")
    url = f"{SERVER_URL}/telemetry"
    headers = {
        "Authorization": f"Bearer {encoded_jwt}",
    }
    asyncio.create_task(xplat.post_request(url, headers, payload))

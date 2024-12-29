import sys
from typing import Any
from src.settings import API_KEY, PORT, SERVER_IP, USE_SERVER

if USE_SERVER and sys.platform not in ("emscripten", "wasm"):
    import requests  # type: ignore[import-untyped]


BAD_API_KEY = "9"

PLAY_TOKEN = "321"
BAD_PLAY_TOKEN_1 = "9"
BAD_PLAY_TOKEN_2 = "zzz"

DUMMY_TELEMETRY_DATA = {"self_assessment": "ok"}


def authn(play_token: str, api_key: str = API_KEY) -> Any:
    resp = requests.post(
        url=f"{SERVER_IP}:{PORT}/authn",
        headers={"x-api-key": api_key},
        json={"play_token": play_token},
    )
    try:
        resp_json = resp.json()
    except:  # noqa E722
        resp_json = {}

    # print(f"{resp.url=}, {resp.status_code=}, {resp_json=}")
    return resp_json


#####################################################################


def send_telemetry(encoded_jwt: str, telemetry: Any, api_key: str = API_KEY) -> Any:
    resp2 = requests.post(
        url=f"{SERVER_IP}:{PORT}/telemetry",
        headers={"x-api-key": api_key, "Authorization": f"Bearer {encoded_jwt}"},
        json={"telemetry_data": telemetry},
    )

    try:
        resp_json = resp2.json()
    except:  # noqa E722
        resp_json = {}

    # print(resp2.url, resp2.status_code, resp_json)

    return resp_json


if __name__ == "__main__":
    # test with bad api key and good token
    resp_bad = authn(PLAY_TOKEN, api_key=BAD_API_KEY)
    # test with bad token and good api key
    resp_bad = authn(BAD_PLAY_TOKEN_1)
    # test with good api key and token
    resp = authn(PLAY_TOKEN)

    # test telemetry with bad token (wrong value)
    resp3 = send_telemetry(BAD_PLAY_TOKEN_1, DUMMY_TELEMETRY_DATA)
    # test telemetry with bad token (wrong type)
    resp4 = send_telemetry(BAD_PLAY_TOKEN_2, DUMMY_TELEMETRY_DATA)

    print(resp)
    encoded_jwt = resp["jwt"]
    resp5 = send_telemetry(encoded_jwt, DUMMY_TELEMETRY_DATA, api_key=BAD_API_KEY)

    # test telemetry with good token
    resp2 = send_telemetry(encoded_jwt, DUMMY_TELEMETRY_DATA)

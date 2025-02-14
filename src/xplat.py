"""Cross-platform utilities.

Credit to
https://github.com/pygame-web/pygbag/blob/1d3b6c9feed9ac79ced18ebea018df9095c1befa/src/pygbag/support/cross/aio/fetch.py
for the general approach to building these cross-platform utilities.
"""

import asyncio
import json
import logging
import platform
import sys
import urllib.request
from typing import Callable


class Log:
    """Simple cross-platform mechanism to print log messages."""

    def __init__(self):
        self.logger_func = None
        self.is_emscripten = sys.platform == "emscripten"
        if self.is_emscripten:
            self._init_emscripten()
        else:
            self._init_default()

    def _init_default(self) -> None:
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=logging.INFO,
        )
        self.logger_func = logging.getLogger(__name__).info

    def _init_emscripten(self) -> None:
        js_code = """
window._LOG = {}
window._LOG.info = function * info(message)
{
    console.log(`${message}`);
    yield
}
"""
        platform.eval(js_code)

        async def _logger(msg: str) -> None:
            await platform.jsiter(platform.window._LOG.info(msg))

        self.logger_func = _logger

    def log(self, message: str):
        if self.is_emscripten:
            asyncio.run(self.logger_func(message))
        else:
            self.logger_func(message)


_LOG: Log = None


def _get_logger() -> Log:
    global _LOG
    if _LOG is None:
        _LOG = Log()
    return _LOG


def log(message: str) -> None:
    """Cross platform logging helper function.

    For desktop, use the `logging` module. For emscripten/web, use a custom
    solution for console logging.
    """
    logger = _get_logger()
    logger.log(message)


class HttpHandler:
    """Utility class for making basic HTTP requests.

    Used for communicating with the game's backend services.
    """

    def __init__(self):
        self.is_emscripten = sys.platform == "emscripten"
        if self.is_emscripten:
            self._init_emscripten()

    def _init_emscripten(self):
        js_code = """
window._HTTP_HANDLER = {}

window._HTTP_HANDLER.get = function * get(
        url,
        headers_json_encoded) {
    var headers = JSON.parse(headers_json_encoded);
    var request = new Request(
        url,
        {
            method: "GET",
            headers: headers
        }
    );
    var content = "";
    fetch(request)
        .then(response => response.text())
        .then((response) => {
            content = response;
        })
        .catch(err => {
            console.log(err);
        });
    while(content == "") {
        yield;
    }

    yield content;
}

window._HTTP_HANDLER.post = function * post(
        url,
        headers_json_encoded,
        payload_json_encoded) {
    // Headers needs to be an object in this context.
    var headers = JSON.parse(headers_json_encoded);
    // Payload should not be an object; we expect a JSON-encoded string here.
    var payload = payload_json_encoded;
    var request = new Request(
        url,
        {
            method: "POST",
            headers: headers,
            body: payload
        }
    );
    var content = "";
    fetch(request)
        .then(response => response.text())
        .then((response) => {
            content = response
        })
        .catch(err => {
            console.log(err);
        });
    while(content == "") {
        yield;
    }
    yield content;
}
"""
        platform.eval(js_code)

        async def _emscripten_get(url: str, headers: dict) -> list | dict:
            # TODO: no utf-8 encoding?
            headers_json_encoded = json.dumps(headers)
            log(f"GET {url}: sending...")
            response = await platform.jsiter(
                platform.window._HTTP_HANDLER.get(url, headers_json_encoded)
            )
            log(f"GET {url}: complete")
            return json.loads(response)

        async def _emscripten_post(
            url: str, headers: dict, payload: list | dict
        ) -> list | dict:
            # TODO: no utf-8 encoding?
            headers_json_encoded = json.dumps(headers)
            payload_json_encoded = json.dumps(payload)
            log(f"POST {url}: sending...")
            response = await platform.jsiter(
                platform.window._HTTP_HANDLER.post(
                    url,
                    headers_json_encoded,
                    payload_json_encoded,
                )
            )
            log(f"POST {url}: complete")
            return json.loads(response)

        self._emscripten_get = _emscripten_get
        self._emscripten_post = _emscripten_post

    async def get(self, url: str, headers: dict = None) -> list | dict:
        """Make a GET request to the given URL, return JSON decoded response."""
        if headers is None:
            headers = {}

        if self.is_emscripten:
            # TODO: prob need async io run call here
            return await self._emscripten_get(url, headers)
        else:
            return await self._default_get(url, headers)

    async def _default_get(self, url: str, headers: dict) -> list | dict:
        request = urllib.request.Request(
            url,
            headers=headers,
            method="GET",
        )
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data

    async def post(self, url: str, headers: dict, data: dict) -> dict:
        """Make a POST request to the given URL, return JSON decoded response."""
        log(f"POST {url}: {data}")
        if headers is None:
            headers = {}
        if data is None:
            data = {}

        if self.is_emscripten:
            # TODO: probably need async io run call here
            return await self._emscripten_post(url, headers, data)
        else:
            return await self._default_post(url, headers, data)

    async def _default_post(self, url: str, headers: dict, data: dict) -> list | dict:
        encoded_data = json.dumps(data).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=encoded_data,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data


_HTTP_HANDLER: HttpHandler = None


def _get_http_handler() -> HttpHandler:
    global _HTTP_HANDLER
    if _HTTP_HANDLER is None:
        _HTTP_HANDLER = HttpHandler()
    return _HTTP_HANDLER


async def get_request(url: str, headers: dict) -> list | dict:
    handler = _get_http_handler()
    return await handler.get(url, headers)


async def post_request(url: str, headers: dict, data: dict) -> list | dict:
    handler = _get_http_handler()
    return await handler.post(url, headers, data)


async def post_request_with_callback(
    url: str,
    headers: dict,
    data: dict,
    callback: Callable[[dict], None],
) -> None:
    # Send the reponse to the callback
    response = await post_request(url, headers, data)
    callback(response)

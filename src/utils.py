import json
import typing
import urllib
from abc import abstractmethod
from collections.abc import Callable
from os import PathLike as _PathProtocol
from typing import IO, Protocol, TextIO, TypeVar, Union

from pygame.color import Color
from pygame.rect import FRect, Rect

from src import xplat

_DOUBLE_SLASH = "//"


# originally authored by pydew-j
def patch_windows_utf8():
    """
    On Windows, files are opened with the system locale, not with UTF-8. This leads to problems
    with umlauts such as 'ü'. See https://dev.to/methane/python-use-utf-8-mode-on-windows-212i.
    It's not possible to set os.environ["PYTHONUTF8"] = "1" in code, because that env var is checked
    at startup time already. This function thus hackily replaces the open() function and adds
    encoding='utf8' to all text-based file opens. It would be possible to add this to every individual
    call, but it's very error-prone to forget, especially since it works on Linux and macOS.

    Also, moving this function to another module can be tricky due to import order and `open()` already
    being called in other modules. If moved, re-test on Windows.
    """

    import builtins
    import os
    import sys

    # If UTF-8 mode already set or not running on Windows: nothing to do
    if sys.platform != "win32" or os.getenv("PYTHONUTF8") == "1":
        return

    original_open = builtins.open

    # Override open() to enforce UTF-8 by default, except for binary modes.
    def utf8_open(*args, **kwargs):
        mode = args[1] if len(args) > 1 else kwargs.get("mode", "r")

        # Apply encoding only if the mode is text (not binary)
        if "b" not in mode and "encoding" not in kwargs:
            kwargs["encoding"] = "utf-8"

        return original_open(*args, **kwargs)

    # Apply the override globally
    builtins.open = utf8_open


# hacky fix for now
patch_windows_utf8()


class JSONWithCommentsDecoder(json.JSONDecoder):
    """JSON Decoder which allows comments starting with //.

    Comments are not preserved. They are simply useful to document
    input files.
    """

    def decode(self, s: str) -> typing.Any:
        # import pdb; pdb.set_trace()
        lines = s.split("\n")
        # filter out any line with leading //
        lines = (line for line in lines if not line.strip().startswith(_DOUBLE_SLASH))

        # ignore any text on a line after a //
        lines = [line.split(_DOUBLE_SLASH, maxsplit=1)[0] for line in lines]

        s = "\n".join(lines)
        return super().decode(s)


def json_loads(s: str, **kwargs) -> typing.Any:
    """Helper function to decode a JSON string.

    JSON inputs can contain comments beginning with //.

    Wrapper function for `json.loads`, with custom decoder.
    """
    return json.loads(s, cls=JSONWithCommentsDecoder, **kwargs)


def json_load(stream: TextIO, **kwargs) -> typing.Any:
    """Helper function to decode a JSON file.

    JSON inputs can contain comments beginning with //.

    Wrapper function for `json.load`, with custom decoder.
    """
    return json.load(stream, cls=JSONWithCommentsDecoder, **kwargs)


URL: str = "https://oxpvhqou52.execute-api.eu-central-2.amazonaws.com/default/telemetry"
_JWT: str | None = None


def get_credentials() -> str:
    global _JWT
    # if not logged in:
    #   send play token and get a JWT back
    #   cache the JWT
    # return the cached JWT
    pass


def send_telemetry(url: str, jwt: str, data: dict):
    import js

    js.console.log("sending telemetry")
    print("sending telemetry")
    headers = {
        "Authorization": f"Bearer {jwt}",
        "x-api-key": "tAXb3oVtqI6KBO6p9Ca1M3TdPCcYj021aUwU6QKc",
    }
    payload = json.dumps(data).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
    )
    for header_name, header_value in sorted(headers.items()):
        request.add_header(header_name, header_value)

    try:
        with urllib.request.urlopen(request) as response:
            response_data = response.read().decode("utf-8")
            print(f"Response status: {response.status}")
            print(f"Response data: {response_data}")
    except urllib.request.HTTPError as e:
        # TODO: error handling
        print(f"HTTP Error: {e.code} - {e.reason}")
        js.console.log(f"HTTP Error: {e.code} - {e.reason}")
    except urllib.request.URLError as e:
        # TODO: error handling
        print(f"URL Error: {e.reason}")
        js.console.log(f"URL Error: {e.reason}")


def log(message: str) -> None:
    """Cross platform logging helper function.

    Basically, just print a message to the console.
    """
    return xplat.log(message)


# Recreate the typing here (code picked from pygame.typing)

# For functions that take a file name
_PathLike = Union[str, bytes, _PathProtocol[str], _PathProtocol[bytes]]
# Most pygame functions that take a file argument should be able to handle a FileLike type
FileLike = Union[_PathLike, IO[bytes], IO[str]]

_T_co = TypeVar("_T_co", covariant=True)


class SequenceLike(Protocol[_T_co]):
    """
    Variant of the standard `Sequence` ABC that only requires `__getitem__` and `__len__`.
    """

    @abstractmethod
    def __getitem__(self, index: int, /) -> _T_co: ...

    @abstractmethod
    def __len__(self) -> int: ...


# Modify typehints when it is possible to annotate sizes

# Pygame handles float without errors in most cases where a point is expected,
# usually rounding to int. Also, 'Union[int, float] == float'
Point = SequenceLike[float]
# This is used where ints are strictly required
IntPoint = SequenceLike[int]

ColorLike = Union[Color, SequenceLike[int], str, int]


class _HasRectAttribute(Protocol):
    # An object that has a rect attribute that is either a rect, or a function
    # that returns a rect conforms to the rect protocol
    @property
    def rect(self) -> Union["RectLike", Callable[[], "RectLike"]]: ...


RectLike = Union[
    Rect, FRect, SequenceLike[float], SequenceLike[Point], _HasRectAttribute
]

# cleanup namespace
del (
    abstractmethod,
    Color,
    Rect,
    FRect,
    IO,
    Callable,
    Union,
    TypeVar,
    Protocol,
)

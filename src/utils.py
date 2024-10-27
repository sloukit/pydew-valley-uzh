import json
import typing
from collections import defaultdict
from collections.abc import Callable

_DOUBLE_SLASH = "//"


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


_KT = typing.TypeVar("_KT")
_VT = typing.TypeVar("_VT")


class DefaultCallableDict(defaultdict):
    default_factory: Callable[[_KT], _VT]

    def __init__(self, callback: Callable[[_KT], _VT]):
        super().__init__(callback)  # noqa

    def __missing__(self, key: _KT):
        value = self.default_factory(key)
        self[key] = value
        return value

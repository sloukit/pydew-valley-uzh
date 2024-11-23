import datetime as dt
from typing import Optional


def parse_cell(key, value: Optional[str]):
    # Verbatim texts, unchanged apart from trim.
    if key.endswith("_text"):
        return _parse_text(value)

    # For others, remove trailing [...] comments.
    value = _strip_trailing_brackets(value)

    if key.endswith("_list"):
        return _parse_text_list(value)

    if key.endswith("_timestamp"):
        return _parse_timestamps(value)

    if key.endswith("_duration"):
        return _parse_duration(value)

    # No specific suffix: treat as bool
    return _parse_bool(value)


def _parse_text(value: Optional[str]) -> str:
    if value is None:
        return ""

    return value.strip()


def _parse_text_list(value: Optional[str]) -> list[str]:
    if value is None:
        return []

    return [
        _parse_text(s)
        for s in value.split(sep=',')
    ]


def _parse_timestamps(value: str | dt.time) -> list[int]:
    if value is None:
        # raise ValueError("Expected timestamp, got empty cell")
        return []

    if isinstance(value, dt.time):
        return [_to_seconds(value, from_excel=True)]

    if not isinstance(value, str):
        raise ValueError(f"Invalid timestamp: {value} -- type {type(value)}")

    return [
        _parse_timestamp(ts)
        # Split commas
        for ts in value.split(sep=',')
    ]


def _parse_timestamp(value: str) -> int:
    try:
        value = value.strip()
        parsed_time = dt.datetime.strptime(value, "%M:%S").time()
        return _to_seconds(parsed_time)
    except ValueError:
        raise ValueError(f"Invalid timestamp '{value}'. Allowed format is MM:SS (e.g., 05:04 or 5:04).")


def _to_seconds(time: dt.time | dt.timedelta, from_excel: bool = False) -> int:
    # If Excel encodes a cell as "time", then it interpretes 01:23 as 01:23:00 AM.
    # However, we want it to be 00:01:23 AM (and then convert it to a duration).
    if from_excel:
        minutes = time.hour
        seconds = time.minute
    else:
        minutes = time.minute
        seconds = time.second

    if minutes > 15 or (minutes == 15 and seconds > 0):
        raise ValueError(f"Invalid timestamp '{time}'. Must be < 15:00.")

    return minutes * 60 + seconds


def _parse_duration(value: str) -> int:
    # print(f"parse_duration: '{value}'")
    min_text = value.rstrip("min")
    # print(f"  -> mins: '{mins}'")

    mins = _str_to_num(min_text, f"Invalid duration '{value}'. Must be 'X min'")
    return 60 * mins


def _parse_bool(value: Optional[str]) -> bool:
    if value is None:  # treat empty cells as "no"
        return False

    if not isinstance(value, str):
        raise ValueError(
            f"Invalid boolean '{value}'; use 'Yes', 'No' or leave empty (note: keys without suffix are bool).")

    value = value.strip()
    if value == "Yes":
        return True
    elif value == "No":
        return False
    elif value == "":  # treat empty cells as "no"
        return False
    else:
        raise ValueError(
            f"Invalid boolean '{value}'; use 'Yes', 'No' or leave empty (note: keys without suffix are bool).")


def _strip_trailing_brackets(s: Optional[str]) -> Optional[str]:
    """
    Strips trailing bracketed content (including brackets) from the input string.
    Example: "hello [ world ]" -> "hello".
    """

    # print(f"strip_trailing_brackets: '{s}'")

    # For any non-string types (None, dt.time, ..) return original object and delegate to parsing fns.
    if not isinstance(s, str):
        return s

    s = s.strip()
    idx = s.rfind('[')
    if idx != -1 and s.endswith(']'):
        s = s[:idx].strip()
    return s


def _str_to_num(value: str, error_msg: str):
    try:
        return int(value)
    except ValueError:
        raise ValueError(error_msg)

# -----------------------------------------------
# Some test cases

# print(_parse_timestamp("05:04"))
# print(_parse_timestamp("05:14"))
# # print(_parse_timestamp("05:4"))
# print(_parse_timestamp("14:04"))
# print("---")
#
# print(parse_cell("x", "Yes  "))
# print(parse_cell("x", "Yes  [ok s] "))
# print(parse_cell("x_timestamp", "1:08  [ok s] "))
# print(parse_cell("x_timestamp", "1:08,  3:08  [ok s] "))
# print(parse_cell("x_text", "1:08,  3:08  [ok s] "))

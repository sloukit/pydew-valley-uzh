# Tools

This directory contains tools that help with developing the game, but are not required by the game itself.

## Excel to JSON

The script `excel_to_json.py` reads an Excel file with a roughly defined structure, containing information about
multiple game levels such as texts (in UI, signposts, etc.), game features, or timestamps determining when features
are enabled/disabled.

### Structure and format

The Excel file contains a **key** column with the name of each property. Each row represents a different key.
The data/value columns represent each an individual level.

- Every data cell needs to conform to a certain **data type** so that the converter understands it.
- Keys must have a suffix to indicate a certain data type; those without are interpreted as boolean.
- If an empty cell is encountered, the default value is used.
- Some types allow comments in `[..]` brackets, which are ignored. `Yes [bla bla]` is interpreted as boolean `true`.
- Values are trimmed (leading/trailing whitespace removed).

The following table shows how Excel cell values map to JSON:

| Data type     | Key suffix   | Example values          | JSON result            | JSON default   |
|---------------|--------------|-------------------------|------------------------|----------------|
| Text          | `_text`      | `Some info `            | `"Some info"`          | `""`           |
| List of texts | `_list`      | `Tomato, Carrot`        | `["Tomato", "Carrot"]` | `[]`           |
| Timestamp     | `_timestamp` | `1:05`,<br>`1:05, 2:30` | `[65]`<br>`[65, 150]`  | `[]`           |
| Duration      | `_duration`  | `10 min`                | `600`                  | value required |
| Boolean       | (no suffix)  | `Yes`, `No`             | `true`, `false`        | `false`        |

### Usage

The tool is invoked on the commandline. You need to be in the virtual environment (venv), which can be activated with:
```bash
# Linux / macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

Once in `venv`, the tool can be invoked with:
```bash
python tools/excel_to_json.py path/to/my/file.xlsx
```

The tool will list any formatting/validation errors.
Output file will be written to `out/levels.json`.
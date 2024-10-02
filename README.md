# PyDew Valley

PyDew Valley is a project originally created by ClearCode in Python using pygame-ce.

This expanded version will be used by the [University of Zurich's Department of Psychology](https://www.psychologie.uzh.ch/en.html) in an experimental study in psychology. For more details on the game levels, please [click here](https://docs.google.com/spreadsheets/d/1NAssjrPN4mv3kBC3e5YmJcYkJZLU7450cFR9EhCbfgE/edit?gid=374591304#gid=374591304). This project is due for completion on November 3rd 2024 (Formerly September 1st, 2024).

For more information, please contact s.kittelberger[at]psychologie.uzh.ch.

## Setup Instructions

This project requires Python 3.12 or above.

1. **Clone this repository:**
    ```
    git clone https://github.com/sloukit/pydew-valley-uzh.git
    ```

2. **Create and activate a virtual environment:**

    **Linux/MacOS**
    ```
    python3 -m venv venv
    source venv/bin/activate
    ```
    **For Windows**
    ```
    python -m venv venv
    venv\Scripts\activate
    ```

3. **Install dependencies**
    ```
    pip install -r requirements.txt # For running the game (runtime dependencies)
    pip install -r requirements-dev.txt # For local development
    pip install -r requirements-test.txt # For running tests
    ```

4. Run this project
    ```
    python main.py
    ```

## Local Development

See [CONTRIBUTING.md](./CONTRIBUTING.md) for more information on how contributions can be made.

### Linting and Formatting

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting. Run `pip install -r requirements-dev.txt` to install it and other relevant dependencies.

> [!IMPORTANT]
> **Before opening a PR, please run the following command to ensure that your code is formatted and doesn't upset the Ruff linter:**
> 
> ```sh
> python formatlint.py
> ```
> 
> Or alternatively, run the following commands individually:
> 
> ```sh
> ruff format . && ruff check --include I --fix . #  format code and sort imports
> ruff check . # Run linting and perform fixes accordingly, or use '# noqa: <RULE>' followed by a comment justifying why the rule is ignored
> ```

## Use of AI
We do not to use AI for visual and design tasks.

## Contributing

Please check [CONTRIBUTING.md](./CONTRIBUTING.md) for more information.

## Team

This section is continuously updated.

- [Sophie Kittelberger](https://github.com/sloukit), Project Director
- [larsbutler](https://github.com/larsbutler), Project Director, Game Developer, & Quality Analyst
- [bromeon](https://github.com/bromeon), Project Director, Game Developer, & Quality Analyst
- [novial](https://github.com/novialriptide), Game Developer & Quality Analyst
- [fortwoone](https://github.com/fortwoone), Game Developer & Quality Analyst
- [richkdev](https://github.com/richkdev), Game Developer & Quality Analyst
- [pmp-p](https://github.com/pmp-p), Game Developer & Quality Analyst
- [Daniel Look](https://github.com/MrTup1), Game Developer & Quality Analyst
- [Minaam Zubair](https://github.com/goatmanking), Game Developer & Quality Analyst
- [bydariogamer](https://github.com/bydariogamer), Game Developer
- [Brody Epstein](https://github.com/Eskimo396), Game Developer
- [Danilo Saiu](https://github.com/ultimateownsz), Game Developer
- [TMN_SGR](https://github.com/TMN-SGR), Game Artist
- [Adrienne Bradley](https://github.com/yoadrienne48), Game Artist
- [farg-eh](https://github.com/farg-eh), Game Artist & Game Developer
- [nteinert2005](https://github.com/nteinert2005), Game Artist & Game Developer
- [Evelin Toth](https://github.com/SSnowly), Game Artist & Game Developer
- [Leon](https://github.com/RUposhcat), Game Artist & Game Developer
- [MortalCoder](https://github.com/MortalCoder), Game Musician & Sound Designer
- [asterli6](https://github.com/asterli6), Game Musician & Sound Designer
- [dee-a-go](https://github.com/dee-a-go), Game Developer, Game Musician, & Sound Designer


## Relevant Links

- Project Task List, https://github.com/users/sloukit/projects/1
- Project's Discord Server, https://discord.gg/SuthU2qKaZ
- Pygame Community's Discord Server, https://discord.gg/pygame
- ClearCode's Discord Server, https://discord.gg/Z2C3vnrxef
- Sprout Lands Assets, https://cupnooble.itch.io/sprout-lands-asset-pack
- ClearCode's Video Tutorial, https://www.youtube.com/watch?v=T4IX36sP_0c

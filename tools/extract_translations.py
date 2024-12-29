import os
import sys

from rich import print

# this is needed to prevent ruff sorting imports
if True:
    # this is needed to prevent pygame message in console
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
    from src.settings import GAME_LANGUAGE
    from src.support import load_translations

LANGS = {"en": "🇬🇧", "de": "🇩🇪"}


def read_extracted_strings(file_name: str) -> list[str]:
    path = os.path.join(
        "data",
        "translations",
        file_name,
    )

    print(
        f'[yellow] * [/][blue] loading extracted strings from [magenta]"{path}"[/] ⌛'
    )

    with open(path, "r") as file:
        text = file.read()

    lines = text.splitlines()
    if lines and lines[0] == "":
        lines = lines[1:]

    print(f"[yellow] * [/][blue] loaded [magenta]{len(lines)}[/] strings ✅")

    return lines


def append_new_strings(
    lang: str,
    new_strings: list[str],
    comment: str | None,
    translations_prefix: str = "",
) -> None:
    path = os.path.join(
        "data",
        "translations",
        f"{lang}.txt",
    )

    print(f'[yellow] * [/][blue] appending new strings to [magenta]"{path}"[/] ⌛')

    with open(path, "a") as file:
        if comment:
            file.write(f"\n# {comment}\n\n")
        for new_string in new_strings:
            file.write(f"{new_string}@@{translations_prefix}{new_string}\n")

    # print(f"[yellow] * [/][blue] loaded [magenta]{len(lines)}[/] strings ✅")


def load_existing_translations() -> dict[str, dict[str, str]]:
    translations = {}
    for lang in LANGS:
        print(
            f'[yellow] * [/][blue] loading existing translations for [magenta]"{lang}"[/] {LANGS[lang]}'
        )
        translations[lang] = load_translations(lang)
        print(
            f"[yellow] * [/][blue] loaded [magenta]{len(translations[lang])}[/] translations ✅"
        )

    return translations


def check_existing_translations(translations: dict[str, dict[str, str]]) -> None:
    def compare_dicts(source, dest):
        res = {}
        res["not_in_source"] = {k: source[k] for k in source if k not in dest}
        res["not_in_dest"] = {k: dest[k] for k in dest if k not in source}

        return res

    print("[yellow] * [/][blue] checking current translations ⌛")
    base_translations = translations[GAME_LANGUAGE]
    for lang in LANGS:
        if lang != GAME_LANGUAGE:
            other_translations = translations[lang]
            result = compare_dicts(base_translations, other_translations)
            got_errors = False
            for key in result["not_in_source"]:
                print(
                    f' 🔴 [red]string present in [magenta]"{lang}"[/] '
                    f'and not present in [magenta]"{GAME_LANGUAGE}"[/]: "[magenta]{key}[/]"'
                )
                got_errors = True
            for key in result["not_in_dest"]:
                print(
                    f' 🔴 [red]string present in [magenta]"{GAME_LANGUAGE}"[/] '
                    f'and not present in [magenta]"{lang}"[/]: "[magenta]{key}[/]"'
                )
                got_errors = True
            if got_errors:
                print("\n[red]fix above problems before continuing❗\n")
                exit(1)
    print("[yellow] * [/][blue] current translations look good ✅")
    return


def process_extracted_strings(
    translations: dict[str, dict[str, str]],
    extracted_strings: list[str],
    comment: str | None,
) -> None:
    new_strings = []
    print("[yellow] * [/][blue] searching for new strings ⌛")
    for extracted_string in extracted_strings:
        if extracted_string not in translations[GAME_LANGUAGE]:
            # print(f"[blue]  found new string: {extracted_string}")
            new_strings.append(extracted_string)
    if len(new_strings) == 0:
        print("[yellow] * [/][blue] no new strings found ⚠️")
    else:
        print(
            f"[yellow] * [/][blue] found [magenta]{len(new_strings)}[/] new strings ✅"
        )
        append_new_strings(GAME_LANGUAGE, new_strings, comment)
        for lang in LANGS:
            if lang != GAME_LANGUAGE:
                append_new_strings(
                    lang,
                    new_strings,
                    comment,
                    translations_prefix=f"{GAME_LANGUAGE.upper()}: ",
                )


def main(comment: str | None) -> None:
    translations = load_existing_translations()
    check_existing_translations(translations)
    extracted_strings = read_extracted_strings("extracted_strings.txt")

    process_extracted_strings(translations, extracted_strings, comment)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        comment = sys.argv[1]
    else:
        comment = None
    main(comment)

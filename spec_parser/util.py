import re
from typing import Pattern, cast


def _replace_text_link(match: re.Match) -> str:
    # [text](link)         ->  text <link>
    # [text](insite_link)  ->  text
    # [link](link)         ->  <link>
    text = str(match.group(1))
    link = str(match.group(2))
    if text.lower() == link.lower():
        return f"<{link}>"
    elif link.startswith("."):
        return f"{text}"
    else:
        return f"{text} <{link}>"


_replace_pairs = {
    "text_link": {"pat": re.compile(r"\[(.*?)\]\((.*?)\)"), "repl": _replace_text_link},
    "code_block_markup": {"pat": re.compile(r"^```\S*\s*$", re.MULTILINE), "repl": ""},
    "code_inline_markup": {"pat": re.compile(r"`([^`]+)`"), "repl": r"\1"},
}


def unmarkdown(text: str) -> str:
    for pair in _replace_pairs.values():
        text = cast(Pattern, pair["pat"]).sub(pair["repl"], text)
    return text

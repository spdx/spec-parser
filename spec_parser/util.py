import re
from typing import Pattern, cast


def _unmarkdown_repl_text_url(match: re.Match) -> str:
    # [text](url)  ->  text <url>
    # [text](url)  ->  text
    # [url](url)   ->  <url>
    text = str(match.group(1))
    url = str(match.group(2))
    if text.lower() == url.lower():
        return f"<{url}>"
    elif url.startswith(".") or url.endswith(".md"):
        return f"{text}"
    else:
        return f"{text} <{url}>"


# A list of regular expression and replacement string pairs, ordered by the
# sequence in which they should be applied to a Markdown text.
# Note that this assumes that the dict is ordered;
# dict is ordered since CPython 3.6 (unofficial) and all of Python 3.7 (official).
_unmakdown_rules = {
    "repl_text_url": {"pat": re.compile(r"\[(.*?)\]\((.*?)\)"), "repl": _unmarkdown_repl_text_url},
    "rm_code_block_markup": {"pat": re.compile(r"^```\S*\s*$", re.MULTILINE), "repl": ""},
    "rm_code_inline_markup": {"pat": re.compile(r"`([^`]+)`"), "repl": r"\1"},
}


def unmarkdown(text: str) -> str:
    """
    Convert Markdown text to plain text by applying a series of
    regular expression replacements.

    Args:
        text (str): The Markdown text to be converted.

    Returns:
        str: The plain text result.
    """
    for pair in _unmakdown_rules.values():
        text = cast(Pattern, pair["pat"]).sub(pair["repl"], text)
    return text

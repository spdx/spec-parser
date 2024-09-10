from __future__ import annotations

import re
from typing import Callable, Pattern, Tuple, Union

ReplaceTuple = Tuple[Pattern[str], Union[str, Callable[[re.Match], str]]]


def _unmarkdown_repl_text_url(match: re.Match) -> str:
    """
    Replacement function for Markdown links.

    [text](url)  ->  text <url>
    [text](url)  ->  text
    [url](url)   ->  <url>
    """
    text = str(match.group(1))
    url = str(match.group(2))
    if text.lower() == url.lower():
        return f"<{url}>"
    elif url.startswith(".") or url.endswith(".md"):
        return f"{text}"
    else:
        return f"{text} <{url}>"


_unmakdown_rules: list[ReplaceTuple] = [
    (re.compile(r"\[(.*?)\]\((.*?)\)"), _unmarkdown_repl_text_url),  # [text](url) replacements
    (re.compile(r"^```\S*\s*$", re.MULTILINE), ""),  # remove code block markup
    (re.compile(r"`([^`]+)`"), r"\1"),  # remove code inline markup
]


def unmarkdown(text: str) -> str:
    """
    Convert Markdown text to plain text by applying a series of
    regular expression replacements.

    Args:
        text (str): The Markdown text to be converted.

    Returns:
        str: The plain text result.
    """
    for pattern, replacement in _unmakdown_rules:
        text = pattern.sub(replacement, text)
    return text

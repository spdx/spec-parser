# SPDX-License-Identifier: Apache-2.0

"""
This module provides utility functions.

Functions:
    unmarkdown(text: str) -> str: Convert Markdown text to plain text.

Types:
    ReplaceTuple: A tuple containing a compiled regex pattern and a replacement string or function.
"""

from __future__ import annotations

import re
from typing import Callable, Pattern, Tuple, Union

ReplaceTuple = Tuple[Pattern, Union[str, Callable[[re.Match], str]]]


def _unmarkdown_repl_text_url(match: re.Match) -> str:
    """
    Replacement function for Markdown links.

    [text](url)         ->  text <url>
    [text](../file.md)  ->  text
    [url](url)          ->  <url>
    """
    text = str(match.group(1))
    url = str(match.group(2))
    if text.lower() == url.lower():
        return f"<{url}>"
    elif url.startswith(".") or url.endswith(".md"):
        return f"{text}"
    else:
        return f"{text} <{url}>"


# A list of (regular expression, replacement string/function), ordered by
# the sequence in which they should be applied to a Markdown text.
_unmakdown_rules: list[ReplaceTuple] = [
    # [text](url) replacements
    (re.compile(r"\[(.*?)\]\((.*?)\)"), _unmarkdown_repl_text_url),
    # remove code block markup
    (re.compile(r"^```\S*\s*\n?", re.MULTILINE), ""),
    # remove code inline markup
    (re.compile(r"`([^`]+)`"), r"\1"),
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

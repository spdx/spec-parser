import os
import re
import logging
from os import path
from typing import List, Tuple
from .config import valid_metadata_key, valid_format_key


def addErrorFilter(logger: logging.Logger) -> None:
    """Add `ErrorFilter` to `logger`

    Args:
        logger (logging.Logger): Add `ErrorFilter` to this logger
    """
    for handler in logger.handlers:
        handler.addFilter(ErrorFoundFilter())
        break


class ErrorFoundFilter(logging.Filter):
    """Filter that store the most severe msg level
    of logging.
    """

    def __init__(self):
        self.worst_level = logging.INFO

    def filter(self, record):
        if record.levelno > self.worst_level:
            self.worst_level = record.levelno
        return True


def isError():
    """Returns `True` if any error was reported by logging.

    Returns:
        bool: `True` if error was reported else `False`.
    """
    logger = logging.getLogger()
    for handler in logger.handlers:
        for filter in handler.filters:
            if isinstance(filter, ErrorFoundFilter):
                return filter.worst_level >= logging.ERROR
    return False


def safe_open(fname: str, *args):
    """Open "fname" after creating neccessary nested directories as needed.

    Args:
        fname (str): path to file

    Returns:
        FileIO: return stream
    """

    dname = os.path.dirname(fname) if os.path.dirname(fname) != "" else "./"
    os.makedirs(dname, exist_ok=True)
    return open(fname, *args)


def safe_listdir(dname: str) -> List[str]:
    """Return a list containing the names of the files in the directory
    and returns empty list if directory doesn't exist.

    Args:
        dname (str): path to directory

    Returns:
        List[str]: list containing the names of the files in the directory
    """
    if path.exists(dname) and path.isdir(dname):
        return os.listdir(dname)
    return []


def union_dict(d1: dict, d2: dict) -> dict:
    """Concat two dict d1, d2, inplace.
    Values in dict d1 will be given priority over dict d2.

    Args:
        d1 (dict): Dict A
        d2 (dict): Dict B

    Returns:
        dict: Dict A+B
    """
    for k, v in d2.items():
        if not k in d1:
            d1[k] = v


def reg_ex_for_section(title: str) -> str:
    return r"((?<=\n)|^)\#{2}\s+" + title + r"(?:(?!\n)\s)*(\n+|$)"


def determine_section_title(parsed_title: str) -> Tuple[List[str], str]:
    if "Metadata" in parsed_title:
        return valid_metadata_key, "metadata"
    elif "Format" in parsed_title:
        return valid_format_key, "format"
    else:
        logging.error("Parsed section is neither metadata nor format.")

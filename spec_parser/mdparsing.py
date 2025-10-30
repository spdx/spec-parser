# parsing the spec .md files

# SPDX-License-Identifier: Apache-2.0

import logging
import re

logger = logging.getLogger(__name__)

class SpecFile:
    RE_SPLIT_TO_SECTIONS = re.compile(r"\n(?=(?:\Z|# |## ))")
    RE_EXTRACT_LICENSE = re.compile(r"\s*SPDX-License-Identifier\s*:\s+(.+)\s*")
    RE_EXTRACT_NAME = re.compile(r"#\s+(\w+)\s*")
    RE_EXTRACT_HEADER_CONTENT = re.compile(r"##\s+(.*)\s+((.|\s)+)")

    def __init__(self, fpath=None):
        self.license = None
        self.sections = dict()
        if fpath is not None:
            self.load(fpath)

    def load(self, fpath):
        logger.debug(f"### loading {fpath.parent}/{fpath.name}")
        filecontent = fpath.read_text(encoding="utf-8")

        parts = re.split(self.RE_SPLIT_TO_SECTIONS, filecontent)

        m = re.fullmatch(self.RE_EXTRACT_LICENSE, parts[0])
        if m is None:
            logger.error(f"File {fpath!s} does not start with license.")
        else:
            self.license = m.group(1)

        m = re.fullmatch(self.RE_EXTRACT_NAME, parts[1])
        if m is None:
            logger.error(f"File {fpath!s} does not have name after license.")
        else:
            self.name = m.group(1)

        for p in parts[2:]:
            if p.strip():
                m = re.fullmatch(self.RE_EXTRACT_HEADER_CONTENT, p)
                if m is None:
                    logging.error(f"File {fpath!s} may contain an empty section at `{p}'")
                else:
                    header = m.group(1)
                    content = m.group(2).strip()
                    if content:
                        self.sections[header] = content
                    else:
                        logging.error(f"Content under header `{header}' in File {fpath!s} is empty.")


class Section:
    def __init__(self, content, filename=None, context=None):
        self.filename = filename
        self.context = context

        if content is not None:
            self.load(content)

    def _fmt_err_msg(self, s, line_num, line_content):
        return f"{s} in {self.context} of '{self.filename}', line {line_num}: `{line_content}'"


class ContentSection(Section):
    def load(self, content):
        self.content = content


class SingleListSection(Section):
    RE_EXTRACT_KEY_VALUE = re.compile(r"-\s+(\w+):\s+(.+)")

    def load(self, content):
        self.content = content
        self.kv = dict()
        for i,l in enumerate(content.splitlines()):
            m = re.fullmatch(self.RE_EXTRACT_KEY_VALUE, l)
            if m is None:
                logger.error(self._fmt_err_msg("Single list parsing error", i+1, l))
            else:
                key = m.group(1)
                val = m.group(2).strip()
                self.kv[key] = val


class NestedListSection(Section):
    RE_EXTRACT_TOP_LEVEL = re.compile(r"-\s+((\w|/)+)")
    RE_EXTRACT_KEY_VALUE = re.compile(r"\s+-\s+(\w+):\s+(.+)")

    def load(self, content):
        self.content = content
        self.ikv = dict()
        for i,l in enumerate(content.splitlines()):
            if l.startswith("-"):
                m = re.fullmatch(self.RE_EXTRACT_TOP_LEVEL, l)
                if m is None:
                    logger.error(self._fmt_err_msg("Top-level nested list parsing error", i+1, l))
                else:
                    item = m.group(1)
                    self.ikv[item] = dict()
            else:
                m = re.fullmatch(self.RE_EXTRACT_KEY_VALUE, l)
                if m is None:
                    logger.error(self._fmt_err_msg("Nested list parsing error", i+1, l))
                else:
                    key = m.group(1)
                    val = m.group(2).strip()
                    self.ikv[item][key] = val

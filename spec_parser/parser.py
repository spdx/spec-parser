import logging
import re
import sys
import sly
from sly import Parser, Lexer
from .config import valid_dataprop_key, valid_metadata_key

__all__ = ["MDLexer", "MDClass", "MDProperty", "MDVocab"]


def get_line(text: str, t: int):
    lineno = text.count("\n", 0, t) + 1
    last_cr = text.rfind("\n", 0, t)
    if last_cr < 0:
        last_cr = 0
    column = (t - last_cr) + 1
    return lineno, column


def parser_error(self, p, msg=None):
    self.isError = True

    fname = getattr(self.lexer, "fname", "<unknown>")
    text = getattr(self.lexer, "text", "")
    index = getattr(p, "index", 0)

    l, c = get_line(text, index)
    if isinstance(p, sly.lex.Token):
        self.log.error(
            f'{fname}:Ln {l},Col {c}: {msg if msg is not None else "Syntax Error"}\n\t Line no {l}: {repr(p.value)}'
        )
    elif msg is not None:
        self.log.error(f"{self.fname}:Ln {l},Col {c}: {p}\n\t {msg}")
    else:
        self.log.error(f"{self.fname}:Ln {l},Col {c}: {p}")
    return None


class MDLexer(Lexer):
    """Common Lexer for specification input files."""

    log = logging.getLogger("Parser.MDLexer")
    log.setLevel(logging.ERROR)

    tokens = {
        H1,
        H2,
        H3,
        H4,
        H5,
        H6,
        DESCRIPTION,
        SUMMARY,
        METADATA,
        PROPERTIES,
        EXTERNAL_PROPERTIES_RESTRICTIONS,
        ENTRIES,
        LICENSE,
        H_TEXTLINE,
        TEXTLINE,
        ULISTA,
        ULISTB,
        NEWLINE,
    }

    ignore_comment = r"(?:(?!\n)\s)*<!?--(?:(?!-->)(.|\n|\s))*-->(?:(?!\n)\s)*\n*"

    SUMMARY = r"((?<=\n)|^)\#{2}\s+Summary(?:(?!\n)\s)*(\n+|$)"
    DESCRIPTION = r"((?<=\n)|^)\#{2}\s+Description(?:(?!\n)\s)*(\n+|$)"
    METADATA = r"((?<=\n)|^)\#{2}\s+Metadata(?:(?!\n)\s)*(\n+|$)"
    PROPERTIES = r"((?<=\n)|^)\#{2}\s+Properties(?:(?!\n)\s)*(\n+|$)"
    EXTERNAL_PROPERTIES_RESTRICTIONS = r"((?<=\n)|^)\#{2}\s+External properties restrictions(?:(?!\n)\s)*(\n+|$)"
    ENTRIES = r"((?<=\n)|^)\#{2}\s+Entries(?:(?!\n)\s)*(\n+|$)"
    LICENSE = r"((?<=\n)|^)\s*SPDX-License-Identifier\s*:[^\n]+(?:(?!\n)\s)*(\n+|$)"

    H6 = r"((?<=\n)|^)\s*\#{6}"
    H5 = r"((?<=\n)|^)\s*\#{5}"
    H4 = r"((?<=\n)|^)\s*\#{4}"
    H3 = r"((?<=\n)|^)\s*\#{3}"
    H2 = r"((?<=\n)|^)\s*\#{2}"
    H1 = r"((?<=\n)|^)\s*\#{1}"
    H_TEXTLINE = r"(?<=\#)[^\n]+(\n+|$)"

    ULISTA = r"((?<=\n)|^)[*+-][^\n]+(\n+|$)"
    ULISTB = r"((?<=\n)|^)([ ]{2,4}|\t)[*+-][^\n]+(\n+|$)"

    TEXTLINE = r"((?<=\n)|^)[^\n]+(\n+|$)"
    NEWLINE = r"\n+"

    def error(self, t):
        l, c = get_line(self.text, t)
        fname = getattr(self, "fname", "<unknown>")
        self.log.error(
            f"{fname}:Ln {l},Col {c}: Lexer Error: Illegal character {t.value[0]}"
        )
        self.index += 1


class MDClass(Parser):
    """Parser for `Class` entity."""

    # debugfile = 'parser.out'
    log = logging.getLogger("Parser.MDClass")
    log.setLevel(logging.ERROR)
    tokens = MDLexer.tokens
    lexer = None

    @_("maybe_newlines license_name name maybe_summary maybe_description maybe_metadata maybe_properties maybe_external_properties_restrictions")
    def document(self, p):
        if getattr(self, "isError", False):
            return None
        return (p.name, p.maybe_summary, p.maybe_description, p.maybe_metadata, p.maybe_properties, p.license_name, p.maybe_external_properties_restrictions)

    @_("empty", "LICENSE")
    def license_name(self, p):
        if p[0] is None:
            self.error(p._slice[0], "Error: Missing `SPDX-License-Identifier: <value>`")
            return None

        splitted = re.split(r"\s*:\s", p[0], 1)
        if len(splitted) != 2:
            # report the invalid syntax
            self.error(p._slice[0], "Syntax Error: Expected `SPDX-License-Identifier: <value>`")
            return None
        
        license_name = splitted[-1].strip()
        return license_name

    @_("H1 H_TEXTLINE")
    def name(self, p):
        return p.H_TEXTLINE.strip()

    @_("empty", "summary")
    def maybe_summary(self, p):
        if p[0] is None:
            return ""
        return p[0]

    @_("SUMMARY para")
    def summary(self, p):
        return p.para.strip()

    @_("empty", "description")
    def maybe_description(self, p):
        if p[0] is None:
            return ""
        return p[0]

    @_("DESCRIPTION para")
    def description(self, p):
        return p.para.strip()

    @_("empty", "metadata")
    def maybe_metadata(self, p):
        if p[0] is None:
            return []
        return p[0]

    @_("METADATA metadata_list")
    def metadata(self, p):
        return p.metadata_list

    @_("metadata_list metadata_line", "empty")
    def metadata_list(self, p):
        if len(p) == 2:
            return p.metadata_list + [p.metadata_line]
        return []

    @_("ULISTA")
    def metadata_line(self, p):

        ulista = p.ULISTA

        # strip the md list identifier, ie r'[-*+]'
        ulista = re.split(r"[-*+]", ulista, 1)[-1].strip()

        # strip the key and value in metadata entry, ie. <key>: <value>
        ulista = re.split(r"\s*:\s", ulista, 1)

        if len(ulista) != 2:
            # report the invalid syntax
            self.error(p._slice[0], "Syntax Error: Expected `<key>: <values>`")
            return None

        _key = ulista[0].strip()
        _values = re.split(r"\s", ulista[-1].strip())

        if _key not in valid_metadata_key:
            self.error(p._slice[0], f"Error: Invalid metadata key `{_key}`.")

        if any(map(lambda x: x.get("name", "") == _key, p[-2])):
            self.error(p._slice[0], f"Error: Metadata key `{_key}` already exists.")

        return {"name": _key, "values": _values}

    @_("empty", "properties")
    def maybe_properties(self, p):
        if p[0] is None:
            return []
        return p[0]

    @_("PROPERTIES properties_list")
    def properties(self, p):
        return p.properties_list

    @_("properties_list single_property", "empty")
    def properties_list(self, p):
        if len(p) == 1:
            return []
        return p.properties_list + [p.single_property]

    @_("empty", "external_properties_restrictions")
    def maybe_external_properties_restrictions(self, p):
        if p[0] is None:
            return []
        return p[0]

    @_("EXTERNAL_PROPERTIES_RESTRICTIONS external_properties_restrictions_list")
    def external_properties_restrictions(self, p):
        return p.external_properties_restrictions_list

    @_("external_properties_restrictions_list single_property", "empty")
    def external_properties_restrictions_list(self, p):
        if len(p) == 1:
            return []
        return p.external_properties_restrictions_list + [p.single_property]

    @_("ULISTA avline_list")
    def single_property(self, p):

        ulista = p.ULISTA

        # strip the md list identifier, ie r'[-*+]'
        ulista = re.split(r"[-*+]", ulista, 1)[-1].strip()

        if any(map(lambda x: x.get("name", "") == ulista, p[-3])):
            self.error(p._slice[0], f"Error: Data property `{ulista}` already exists.")

        return {"name": ulista, "values": p.avline_list}

    @_("avline_list avline", "empty")
    def avline_list(self, p):
        if len(p) == 1:
            return []
        return p.avline_list + [p.avline]

    @_("ULISTB")
    def avline(self, p):

        ulistb = p.ULISTB

        # strip the md list identifier, ie r'[-*+]'
        ulistb = re.split(r"[-*+]", ulistb, 1)[-1].strip()

        # strip the key and value in metadata entry, ie. <key>: <values>
        ulistb = re.split(r"\s*:\s", ulistb, 1)

        if len(ulistb) != 2:
            # report the invalid syntax
            self.error(p._slice[0], "Syntax Error: Expected `<key>: <values>`")
            return None

        _key = ulistb[0].strip()
        # split values by whitespaces
        _values = re.split(r"\s", ulistb[-1].strip())

        if _key not in valid_dataprop_key:
            self.error(
                p._slice[0], f"Error: Invalid DataProperty Attribute key `{_key}`."
            )

        if any(map(lambda x: x.get("name", "") == _key, p[-2])):
            self.error(p._slice[0], f"Error: Attribute key '{_key}' already exists")

        return {"name": _key, "values": _values}

    @_("para para_line", "empty")
    def para(self, p):
        if len(p) == 1:
            return ""
        else:
            return f"{p.para}{p.para_line}"

    @_("TEXTLINE", "ULISTA", "ULISTB")
    def para_line(self, p):
        return p[0]

    @_("NEWLINE")
    def newlines(self, p):
        return None

    @_("newlines", "empty")
    def maybe_newlines(self, p):
        if hasattr(self, "isError"):
            self.isError = False
        return None

    @_("")
    def empty(self, p):
        return None

    def error(self, p, msg=None):
        parser_error(self, p, msg)


class MDProperty(Parser):
    """Parser for `Property` entity."""

    # debugfile = 'parser.out'
    log = logging.getLogger("Parser.MDProperty")
    log.setLevel(logging.ERROR)
    tokens = MDLexer.tokens
    lexer = None

    @_("maybe_newlines license_name name maybe_summary maybe_description maybe_metadata")
    def document(self, p):
        if getattr(self, "isError", False):
            return None
        return (p.name, p.maybe_summary, p.maybe_description, p.maybe_metadata, p.license_name)

    @_("empty", "LICENSE")
    def license_name(self, p):
        if p[0] is None:
            self.error(p._slice[0], "Error: Missing `SPDX-License-Identifier: <value>`")
            return None

        splitted = re.split(r"\s*:\s", p[0], 1)
        if len(splitted) != 2:
            # report the invalid syntax
            self.error(p._slice[0], "Syntax Error: Expected `SPDX-License-Identifier: <value>`")
            return None
        
        license_name = splitted[-1].strip()
        return license_name

    @_("H1 H_TEXTLINE")
    def name(self, p):
        return p.H_TEXTLINE.strip()

    @_("empty", "summary")
    def maybe_summary(self, p):
        if p[0] is None:
            return ""
        return p[0]

    @_("SUMMARY para")
    def summary(self, p):
        return p.para.strip()

    @_("empty", "description")
    def maybe_description(self, p):
        if p[0] is None:
            return ""
        return p[0]

    @_("DESCRIPTION para")
    def description(self, p):
        return p.para.strip()

    @_("empty", "metadata")
    def maybe_metadata(self, p):
        if p[0] is None:
            return []
        return p[0]

    @_("METADATA metadata_list")
    def metadata(self, p):
        return p.metadata_list

    @_("metadata_list metadata_line", "empty")
    def metadata_list(self, p):
        if len(p) == 2:
            return p.metadata_list + [p.metadata_line]
        return []

    @_("ULISTA")
    def metadata_line(self, p):

        ulista = p.ULISTA

        # strip the md list identifier, ie r'[-*+]'
        ulista = re.split(r"[-*+]", ulista, 1)[-1].strip()

        # strip the key and value in metadata entry, ie. <key>: <value>
        ulista = re.split(r"\s*:\s", ulista, 1)

        if len(ulista) != 2:
            # report the invalid syntax
            self.error(p._slice[0], "Syntax Error: Expected `<key>: <values>`")
            return None

        _key = ulista[0].strip()
        _values = re.split(r"\s", ulista[-1].strip())

        if _key not in valid_metadata_key:
            self.error(p._slice[0], f"Error: Invalid metadata key `{_key}`.")

        if any(map(lambda x: x.get("name", "") == _key, p[-2])):
            self.error(p._slice[0], f"Error: Metadata key `{_key}` already exists.")

        return {"name": _key, "values": _values}

    @_("para para_line", "empty")
    def para(self, p):
        if len(p) == 1:
            return ""
        else:
            return f"{p.para}{p.para_line}"

    @_("TEXTLINE", "ULISTA", "ULISTB")
    def para_line(self, p):
        return p[0]

    @_("NEWLINE")
    def newlines(self, p):
        return None

    @_("newlines", "empty")
    def maybe_newlines(self, p):
        if hasattr(self, "isError"):
            self.isError = False
        return None

    @_("")
    def empty(self, p):
        return None

    def error(self, p, msg=None):
        parser_error(self, p, msg)


class MDVocab(MDProperty):
    """Parser for `Vocab` entity."""

    # debugfile = 'parser.out'
    log = logging.getLogger("Parser.MDVocab")
    log.setLevel(logging.ERROR)
    tokens = MDLexer.tokens
    lexer = None

    @_("maybe_newlines license_name name maybe_summary maybe_description maybe_metadata maybe_entries")
    def document(self, p):
        if getattr(self, "isError", False):
            return None
        return (p.name, p.maybe_summary, p.maybe_description, p.maybe_metadata, p.maybe_entries, p.license_name)

    @_("empty", "LICENSE")
    def license_name(self, p):
        if p[0] is None:
            self.error(p._slice[0], "Error: Missing `SPDX-License-Identifier: <value>`")
            return None

        splitted = re.split(r"\s*:\s", p[0], 1)
        if len(splitted) != 2:
            # report the invalid syntax
            self.error(p._slice[0], "Syntax Error: Expected `SPDX-License-Identifier: <value>`")
            return None
        
        license_name = splitted[-1].strip()
        return license_name

    @_("H1 H_TEXTLINE")
    def name(self, p):
        return p.H_TEXTLINE.strip()

    @_("empty", "summary")
    def maybe_summary(self, p):
        if p[0] is None:
            return ""
        return p[0]
    
    @_("SUMMARY para")
    def summary(self, p):
        return p.para.strip()

    @_("empty", "description")
    def maybe_description(self, p):
        if p[0] is None:
            return ""
        return p[0]

    @_("DESCRIPTION para")
    def description(self, p):
        return p.para.strip()

    @_("empty", "metadata")
    def maybe_metadata(self, p):
        if p[0] is None:
            return []
        return p[0]

    @_("METADATA metadata_list")
    def metadata(self, p):
        return p.metadata_list

    @_("metadata_list metadata_line", "empty")
    def metadata_list(self, p):
        if len(p) == 2:
            return p.metadata_list + [p.metadata_line]
        return []

    @_("ULISTA")
    def metadata_line(self, p):

        ulista = p.ULISTA

        # strip the md list identifier, ie r'[-*+]'
        ulista = re.split(r"[-*+]", ulista, 1)[-1].strip()

        # strip the key and value in metadata entry, ie. <key>: <value>
        ulista = re.split(r"\s*:\s", ulista, 1)

        if len(ulista) != 2:
            # report the invalid syntax
            self.error(p._slice[0], "Syntax Error: Expected `<key>: <values>`")
            return None

        _key = ulista[0].strip()
        _values = re.split(r"\s", ulista[-1].strip())

        if _key not in valid_metadata_key:
            self.error(p._slice[0], f"Error: Invalid metadata key `{_key}`.")

        if any(map(lambda x: x.get("name", "") == _key, p[-2])):
            self.error(p._slice[0], f"Error: Metadata key `{_key}` already exists.")

        return {"name": _key, "values": _values}

    @_("empty", "entries")
    def maybe_entries(self, p):
        if p[0] is None:
            return []
        return p[0]

    @_("ENTRIES entry_list")
    def entries(self, p):
        return p.entry_list

    @_("entry_list entry_line", "empty")
    def entry_list(self, p):
        if len(p) == 2:
            return p.entry_list + [p.entry_line]
        return []

    @_("ULISTA")
    def entry_line(self, p):

        ulista = p.ULISTA

        # strip the md list identifier, ie r'[-*+]'
        ulista = re.split(r"[-*+]", ulista, 1)[-1].strip()

        # strip the key and value in metadata entry, ie. <key>: <value>
        ulista = re.split(r"\s*:\s", ulista, 1)

        if len(ulista) != 2:
            # report the invalid syntax
            self.error(p._slice[0], "Syntax Error: Expected `<key>: <description>`")
            return None

        _key = ulista[0].strip()
        _value = ulista[-1].strip()

        if any(map(lambda x: x.get("name", "") == _key, p[-2])):
            self.error(p._slice[0], "Error: Entry '{_key}' already exists")

        return {"name": _key, "value": _value}

    @_("para para_line", "empty")
    def para(self, p):
        if len(p) == 1:
            return ""
        else:
            return f"{p.para}{p.para_line}"

    @_("TEXTLINE", "ULISTA", "ULISTB")
    def para_line(self, p):
        return p[0]

    @_("NEWLINE")
    def newlines(self, p):
        return None

    @_("newlines", "empty")
    def maybe_newlines(self, p):
        if hasattr(self, "isError"):
            self.isError = False
        return None

    @_("")
    def empty(self, p):
        return None

    def error(self, p, msg=None):
        parser_error(self, p, msg)


if __name__ == "__main__":

    lexer = MDLexer()
    parser = MDClass()
    parser.lexer = lexer

    fpath = sys.argv[1]
    # fpath = "spec-v3-model/model/Core/Vocabularies/HashAlgorithmVocab.md"
    print(fpath)

    with open(fpath, "r") as f:
        inp = f.read()

    for tok in lexer.tokenize(inp):
        print(tok)

    lexer.fname = fpath
    result = parser.parse(lexer.tokenize(inp))
    result.dump_md("./test.md")

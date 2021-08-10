import logging
import re
import sys
import sly
from sly import Parser, Lexer
from utils import SpecClass, SpecProperty, SpecVocab
from config import valid_dataprop_key, valid_metadata_key


def get_line(text: str, t: int):
    lineno = text.count('\n', 0, t)+1
    last_cr = text.rfind('\n', 0, t)
    if last_cr < 0:
        last_cr = 0
    column = (t - last_cr) + 1
    return lineno, column


def parser_error(self, p, msg=None):
    self.isError = True

    fname = getattr(self.lexer, 'fname', '<unknown>')
    text = getattr(self.lexer, 'text', '')
    index = getattr(p, 'index', 0)

    l, c = get_line(text, index)
    if isinstance(p, sly.lex.Token):
        self.log.error(
            f'{fname}:Ln {l},Col {c}: {msg if msg is not None else "Syntax Error"}\n\t Line no {l}: {repr(p.value)}')
    else:
        self.log.error(f'{self.fname}:Ln {l},Col {c}: {p}')
    return None


class MDLexerBase(Lexer):

    log = logging.getLogger('Parser.MDLexer')

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
        ENTRIES,
        H_TEXTLINE,
        TEXTLINE,
        PROP_LINE,
        ATTR_KEY,
        COLON,
        ATTR_VAL,
        ULISTA,
        ULISTB,
        ULISTA_INIT,
        ULISTB_INIT,
        NEWLINE
    }

    # ignore_comment = r'<!?--(?:(?!-->)(.|\n|\s))*-->\n*'
    ignore_comment = r'[ \t]*<!?--(?:(?!-->)(.|\n|\s))*-->[ \t]*(\n+|$)'

    SUMMARY = r'((?<=\n)|^)\#{2}\s+Summary(?:(?!\n)\s)*(\n+|$)'
    DESCRIPTION = r'((?<=\n)|^)\#{2}\s+Description(?:(?!\n)\s)*(\n+|$)'
    METADATA = r'((?<=\n)|^)\#{2}\s+Metadata(?:(?!\n)\s)*(\n+|$)'
    PROPERTIES = r'((?<=\n)|^)\#{2}\s+Properties(?:(?!\n)\s)*(\n+|$)'
    ENTRIES = r'((?<=\n)|^)\#{2}\s+Entries(?:(?!\n)\s)*(\n+|$)'

    H6 = r'((?<=\n)|^)\s*\#{6}'
    H5 = r'((?<=\n)|^)\s*\#{5}'
    H4 = r'((?<=\n)|^)\s*\#{4}'
    H3 = r'((?<=\n)|^)\s*\#{3}'
    H2 = r'((?<=\n)|^)\s*\#{2}'
    H1 = r'((?<=\n)|^)\s*\#{1}'
    H_TEXTLINE = r'(?<=\#)[^\n]+(\n+|$)'

    def METADATA(self, t):
        self.begin(MDLexerMdata)
        return t

    def PROPERTIES(self, t):
        self.begin(MDLexerProp)
        return t

    def ENTRIES(self, t):
        self.begin(MDLexerEntries)
        return t

    def SUMMARY(self, t):
        self.begin(MDLexer)
        return t

    def DESCRIPTION(self, t):
        self.begin(MDLexer)
        return t

    def H1(self, t):
        self.begin(MDLexer)
        return t

    def error(self, t):
        # l, c = get_line(self.text, t)
        # fname = getattr(self, 'fname', '<unknown>')
        # self.log.error(
        #     f'{fname}:Ln {l},Col {c}: Lexer Error: Illegal character {t.value[0]}')
        print(f'error: {t}')
        self.index += 1


# class MDLexerDesc(MDLexerBase):

#     # derived from base class
#     tokens = {}

#     TEXTLINE = r'((?<=\n)|^)[^\n]+(\n+|$)'
#     NEWLINE = r'\n+'


class MDLexerProp(MDLexerBase):

    # derived from base class
    tokens = MDLexerBase.tokens

    ULISTA_INIT = r'((?<=\n)|^)[*+-]'
    ULISTB_INIT = r'((?<=\n)|^)([ ]{2,4}|\t)[*+-]'
    ATTR_KEY = r'(?<=[*+-])(?:(?!(:[ \t]))[^\n])+(?=:[ \t])'
    PROP_LINE = r'(?<=[*+-])[^\n]+(\n+|$)'
    COLON = r':'
    ATTR_VAL = r'[ \t]+[^\s]+((?:(?!\n)\s)*\n+|$)?'
    NEWLINE = r'\n+'


class MDLexerEntries(MDLexerBase):

    # derived from base class
    tokens = MDLexerBase.tokens

    ULISTA_INIT = r'((?<=\n)|^)[*+-]'
    ATTR_KEY = r'(?<=[*+-])(?:(?!(:[ \t]))[^\n])+(?=(:[ \t]))'
    COLON = r':[ \t]'
    ATTR_VAL = r'(?<=(:[ \t]))[^\n]+(\n+|$)'
    NEWLINE = r'\n+'


class MDLexerMdata(MDLexerBase):

    # derived from base class
    tokens = MDLexerBase.tokens

    ULISTA_INIT = r'((?<=\n)|^)[*+-]'
    ATTR_KEY = r'(?<=[*+-])(?:(?!(:[ \t]))[^\n])+(?=(:[ \t]))'
    COLON = r':[ \t]'
    ATTR_VAL = r'[^\s]+(\s+|$)'
    NEWLINE = r'\n+'


class MDLexer(MDLexerBase):

    # derived from base class
    tokens = MDLexerBase.tokens

    TEXTLINE = r'((?<=\n)|^)[^\n]+(\n+|$)'
    NEWLINE = r'\n+'


class MDClass(Parser):

    # debugfile = 'parser.out'
    log = logging.getLogger('Parser.MDClass')
    tokens = MDLexer.tokens
    lexer = None

    @_('maybe_newlines name summary description metadata properties')
    def document(self, p):
        if getattr(self, 'isError', False):
            return None
        return (p.name, p.summary, p.description, p.metadata, p.properties)

    @_('H1 H_TEXTLINE')
    def name(self, p):
        return p.H_TEXTLINE.strip()

    @_('SUMMARY para')
    def summary(self, p):
        return p.para.strip()

    @_('DESCRIPTION para')
    def description(self, p):
        return p.para.strip()

    @_('METADATA metadata_list')
    def metadata(self, p):
        return p.metadata_list

    @_('metadata_list metadata_line',
        'empty')
    def metadata_list(self, p):
        if len(p) == 2:
            return p.metadata_list+[p.metadata_line]
        return []

    @_('ULISTA_INIT ATTR_KEY COLON attr_vals')
    def metadata_line(self, p):

        _key = p.ATTR_KEY.strip()
        _values = p.attr_vals

        if _key not in valid_metadata_key:
            self.error(p._slice[0], f"Error: Invalid metadata key `{_key}`.")

        if any(map(lambda x: x.get('name', '') == _key, p[-5])):
            self.error(
                p._slice[0], f"Error: Metadata key `{_key}` already exists.")

        return {'name': _key, 'values': _values}

    @_('PROPERTIES properties_list')
    def properties(self, p):
        return p.properties_list

    @_('properties_list single_property',
        'empty')
    def properties_list(self, p):
        if len(p) == 1:
            return []
        return p.properties_list+[p.single_property]

    @_('ULISTA_INIT PROP_LINE avline_list')
    def single_property(self, p):

        # strip the md list identifier, ie r'[-*+]'
        ulista = p.PROP_LINE.strip()

        if any(map(lambda x: x.get('name', '') == ulista, p[-4])):
            self.error(
                p._slice[0], f'Error: Data property `{ulista}` already exists.')

        return {'name': ulista, 'values': p.avline_list}

    @_('avline_list avline',
        'empty')
    def avline_list(self, p):
        if len(p) == 1:
            return []
        return p.avline_list + [p.avline]

    @_('ULISTB_INIT ATTR_KEY COLON attr_vals')
    def avline(self, p):

        _key = p.ATTR_KEY.strip()
        # split values by whitespaces
        _values = p.attr_vals

        if _key not in valid_dataprop_key:
            self.error(
                p._slice[0], f"Error: Invalid DataProperty Attribute key `{_key}`.")

        if any(map(lambda x: x.get('name', '') == _key, p[-5])):
            self.error(
                p._slice[0], f"Error: Attribute key \'{_key}\' already exists")

        return {'name': _key, 'values': _values}

    @_('para TEXTLINE',
        'empty')
    def para(self, p):
        if len(p) == 1:
            return ''
        return f"{p.para}{p.TEXTLINE}"

    @_('attr_vals ATTR_VAL',
        'ATTR_VAL')
    def attr_vals(self, p):
        if len(p) == 1:
            return [p.ATTR_VAL.strip()]
        return p.attr_vals+[p.ATTR_VAL.strip()]

    @_('NEWLINE')
    def newlines(self, p):
        return None

    @_('newlines',
        'empty')
    def maybe_newlines(self, p):
        if hasattr(self, 'isError'):
            self.isError = False
        return None

    @_('')
    def empty(self, p):
        return None

    def error(self, p, msg=None):
        parser_error(self, p, msg)


class MDProperty(Parser):

    # debugfile = 'parser.out'
    log = logging.getLogger('Parser.MDProperty')
    tokens = MDLexerBase.tokens
    lexer = None

    @_('maybe_newlines name summary description metadata')
    def document(self, p):
        if getattr(self, 'isError', False):
            return None
        return (p.name, p.summary, p.description, p.metadata)

    @_('H1 H_TEXTLINE')
    def name(self, p):
        return p.H_TEXTLINE.strip()

    @_('SUMMARY para')
    def summary(self, p):
        return p.para.strip()

    @_('DESCRIPTION para')
    def description(self, p):
        return p.para.strip()

    @_('METADATA metadata_list')
    def metadata(self, p):
        return p.metadata_list

    @_('metadata_list metadata_line',
        'empty')
    def metadata_list(self, p):
        if len(p) == 2:
            return p.metadata_list+[p.metadata_line]
        return []

    @_('ULISTA_INIT ATTR_KEY COLON attr_vals')
    def metadata_line(self, p):

        _key = p.ATTR_KEY.strip()
        _values = p.attr_vals

        if _key not in valid_metadata_key:
            self.error(p._slice[0], f"Error: Invalid metadata key `{_key}`.")

        if any(map(lambda x: x.get('name', '') == _key, p[-5])):
            self.error(
                p._slice[0], f"Error: Metadata key `{_key}` already exists.")

        return {'name': _key, 'values': _values}

    @_('para TEXTLINE',
        'empty')
    def para(self, p):
        if len(p) == 1:
            return ''
        return f"{p.para}{p.TEXTLINE}"

    @_('attr_vals ATTR_VAL',
        'ATTR_VAL')
    def attr_vals(self, p):
        if len(p) == 1:
            return [p.ATTR_VAL.strip()]
        return p.attr_vals+[p.ATTR_VAL.strip()]

    @_('NEWLINE')
    def newlines(self, p):
        return None

    @_('newlines',
        'empty')
    def maybe_newlines(self, p):
        if hasattr(self, 'isError'):
            self.isError = False
        return None

    @_('')
    def empty(self, p):
        return None

    def error(self, p, msg=None):
        parser_error(self, p, msg)


class MDVocab(MDProperty):
    # debugfile = 'parser.out'
    log = logging.getLogger('Parser.MDVocab')
    tokens = MDLexer.tokens
    lexer = None

    @_('maybe_newlines name summary description metadata entries')
    def document(self, p):
        if getattr(self, 'isError', False):
            return None
        return (p.name, p.summary, p.description, p.metadata, p.entries)

    @_('H1 H_TEXTLINE')
    def name(self, p):
        return p.H_TEXTLINE.strip()

    @_('SUMMARY para')
    def summary(self, p):
        return p.para.strip()

    @_('DESCRIPTION para')
    def description(self, p):
        return p.para.strip()

    @_('METADATA metadata_list')
    def metadata(self, p):
        return p.metadata_list

    @_('metadata_list metadata_line',
        'empty')
    def metadata_list(self, p):
        if len(p) == 2:
            return p.metadata_list+[p.metadata_line]
        return []

    @_('ULISTA_INIT ATTR_KEY COLON attr_vals')
    def metadata_line(self, p):

        _key = p.ATTR_KEY.strip()
        _values = p.attr_vals

        if _key not in valid_metadata_key:
            self.error(p._slice[0], f"Error: Invalid metadata key `{_key}`.")

        if any(map(lambda x: x.get('name', '') == _key, p[-5])):
            self.error(
                p._slice[0], f"Error: Metadata key `{_key}` already exists.")

        return {'name': _key, 'values': _values}

    @_('ENTRIES entry_list')
    def entries(self, p):
        return p.entry_list

    @_('entry_list entry_line',
        'empty')
    def entry_list(self, p):
        if len(p) == 2:
            return p.entry_list+[p.entry_line]
        return []

    @_('ULISTA_INIT ATTR_KEY COLON ATTR_VAL')
    def entry_line(self, p):

        _key = p.ATTR_KEY.strip()
        _value = p.ATTR_VAL.strip()

        if any(map(lambda x: x.get('name', '') == _key, p[-5])):
            self.error(
                p._slice[0], 'Error: Entry \'{_key}\' already exists')

        return {'name': _key, 'value': _value}

    @_('para TEXTLINE',
        'empty')
    def para(self, p):
        if len(p) == 1:
            return ''
        return f"{p.para}{p.TEXTLINE}"

    @_('attr_vals ATTR_VAL',
        'ATTR_VAL')
    def attr_vals(self, p):
        if len(p) == 1:
            return [p.ATTR_VAL.strip()]
        return p.attr_vals+[p.ATTR_VAL.strip()]

    @_('NEWLINE')
    def newlines(self, p):
        return None

    @_('newlines',
        'empty')
    def maybe_newlines(self, p):
        if hasattr(self, 'isError'):
            self.isError = False
        return None

    @_('')
    def empty(self, p):
        return None

    def error(self, p, msg=None):
        parser_error(self, p, msg)


if __name__ == '__main__':

    lexer = MDLexer()
    parser = MDClass()
    parser.lexer = lexer

    fpath = sys.argv[1]
    # fpath = "spec-v3-template/model/Core/Vocabularies/HashAlgorithmVocab.md"
    print(fpath)

    with open(fpath, "r") as f:
        inp = f.read()

    for tok in lexer.tokenize(inp):
        print(tok)

    lexer.fname = fpath
    result = parser.parse(lexer.tokenize(inp))
    print(result)

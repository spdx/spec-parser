from utils import *
import sys
import re
from sly import Parser, Lexer


class MyLogger(object):
    def __init__(self, f):
        self.f = f

    def debug(self, msg, *args, **kwargs):
        self.f.write((msg % args) + '\n')

    info = debug

    def warning(self, msg, *args, **kwargs):
        self.f.write('WARNING: ' + (msg % args) + '\n')

    def error(self, msg, *args, **kwargs):
        self.f.write('ERROR: ' + (msg % args) + '\n')

    critical = debug

class MDLexer(Lexer):

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
        TEXTLINE,
        ULISTA,
        ULISTB,
        NEWLINE,
    }

    SUMMARY = r'((?<=\n)|^)\#{2}\s+Summary\s+(\n+|$)'
    DESCRIPTION = r'((?<=\n)|^)\#{2}\s+Description\s+(\n+|$)'
    METADATA = r'((?<=\n)|^)\#{2}\s+Metadata\s+(\n+|$)'
    PROPERTIES = r'((?<=\n)|^)\#{2}\s+Properties\s+(\n+|$)'
    ENTRIES = r'((?<=\n)|^)\#{2}\s+Entries\s+(\n+|$)'

    H6 = r'((?<=\n)|^)\#{6}'
    H5 = r'((?<=\n)|^)\#{5}'
    H4 = r'((?<=\n)|^)\#{4}'
    H3 = r'((?<=\n)|^)\#{3}'
    H2 = r'((?<=\n)|^)\#{2}'
    H1 = r'((?<=\n)|^)\#{1}'

    ULISTA = r'((?<=\n)|^)[*+-][^`*\n\t\\[\]]+(\n+|$)'
    ULISTB = r'((?<=\n)|^)([ ]{2,4}|\t)[*+-][^`\n\t\\[\]]+(\n+|$)'

    TEXTLINE = r'[^`*\n\t\\[\]]+(\n+|$)'

    ignore_comment = r'<!?--(?:(?!-->)(.|\n|\s))*-->\n*'

    @_(r'\n+')
    def NEWLINE(self, t):
        self.lineno += len(t.value)
        return t

    def error(self, t):
        print("Illegal character '%s'" % t.value[0])
        self.index += 1

class MDClass(Parser):

    # debugfile = 'parser.out'
    log = MyLogger(sys.stderr)
    tokens = MDLexer.tokens
    isError = False

    @_('maybe_newlines name summary description metadata properties')
    def document(self, p):
        if self.isError:
            return None
        return SpecClass(p.name, p.summary, p.description, p.metadata, p.properties)

    @_('H1 TEXTLINE')
    def name(self, p):
        return p.TEXTLINE.strip()

    @_('SUMMARY para',
        'empty')
    def summary(self, p):
        if len(p) == 1:
            return None
        return p.para

    @_('DESCRIPTION para',
        'empty')
    def description(self, p):
        if len(p) == 1:
            return None
        return p.para

    @_('METADATA metadata_list',
        'empty')
    def metadata(self, p):
        if len(p) == 1:
            return []
        return p.metadata_list

    @_('metadata_list metadata_line',
        'empty')
    def metadata_list(self, p):
        if len(p) == 2:
            return p.metadata_list+[p.metadata_line]
        return []

    @_('ULISTA')
    def metadata_line(self, p):
        
        ulista = p.ULISTA

        # strip the md list identifier, ie r'[-*+]'
        ulista = re.split(r'[-*+]', ulista, 1)[-1].strip()

        # strip the key and value in metadata entry, ie. <key>: <value>
        ulista = re.split(r'\s*:\s', ulista, 1)

        if len(ulista) != 2:
            # report the invalid syntax
            self.error(p._slice[0])
            return None

        _key = ulista[0].strip()
        _values = re.split(r'\s',ulista[-1].strip())

        return {'name': _key, 'values': _values}

    @_('PROPERTIES properties_list',
        'empty')
    def properties(self, p):
        if len(p) == 1:
            return []
        return p.properties_list

    @_('properties_list single_property',
        'empty')
    def properties_list(self, p):
        if len(p) == 1:
            return []
        return p.properties_list+[p.single_property]

    @_('ULISTA avline_list')
    def single_property(self, p):
        
        ulista = p.ULISTA

        # strip the md list identifier, ie r'[-*+]'
        ulista = re.split(r'[-*+]', ulista, 1)[-1].strip()

        return {'name': ulista, 'values': p.avline_list}

    @_('avline_list avline',
        'avline')
    def avline_list(self, p):
        if len(p) == 1:
            return [p.avline]
        return p.avline_list + [p.avline]

    @_('ULISTB')
    def avline(self, p):
        
        ulistb = p.ULISTB

        # strip the md list identifier, ie r'[-*+]'
        ulistb = re.split(r'[-*+]', ulistb, 1)[-1].strip()

        # strip the key and value in metadata entry, ie. <key>: <values>
        ulistb = re.split(r'\s*:\s', ulistb, 1)

        if len(ulistb) != 2:
            # report the invalid syntax
            self.error(p._slice[0])
            return None

        _key = ulistb[0].strip()

        # split values by whitespaces
        _values = re.split(r'\s',ulistb[-1].strip())

        return {'name': _key, 'values': _values}

    @_('para TEXTLINE',
        'empty')
    def para(self, p):
        if len(p) == 1:
            return ''
        else:
            return f"{p.para} {p.TEXTLINE.strip()}"

    @_('NEWLINE')
    def newlines(self, p):
        return None

    @_('newlines',
        'empty')
    def maybe_newlines(self, p):
        return None

    @_('')
    def empty(self, p):
        return None

    def error(self, p):
        self.isError = True
        print('ERROR: ', p)
        return None

class MDProperty(Parser):

    # debugfile = 'parser.out'
    log = MyLogger(sys.stderr)
    tokens = MDLexer.tokens
    isError = False

    @_('maybe_newlines name summary description metadata')
    def document(self, p):
        if self.isError:
            return None
        return SpecProperty(p.name, p.summary, p.description, p.metadata)

    @_('H1 TEXTLINE')
    def name(self, p):
        return p.TEXTLINE.strip()

    @_('SUMMARY para',
        'empty')
    def summary(self, p):
        if len(p) == 1:
            return None
        return p.para

    @_('DESCRIPTION para',
        'empty')
    def description(self, p):
        if len(p) == 1:
            return None
        return p.para

    @_('METADATA metadata_list',
        'empty')
    def metadata(self, p):
        if len(p) == 1:
            return []
        return p.metadata_list

    @_('metadata_list metadata_line',
        'empty')
    def metadata_list(self, p):
        if len(p) == 2:
            return p.metadata_list+[p.metadata_line]
        return []

    @_('ULISTA')
    def metadata_line(self, p):
        
        ulista = p.ULISTA

        # strip the md list identifier, ie r'[-*+]'
        ulista = re.split(r'[-*+]', ulista, 1)[-1].strip()

        # strip the key and value in metadata entry, ie. <key>: <value>
        ulista = re.split(r'\s*:\s', ulista, 1)

        if len(ulista) != 2:
            # report the invalid syntax
            self.error(p._slice[0])
            return None

        _key = ulista[0].strip()
        _values = re.split(r'\s',ulista[-1].strip())

        return {'name': _key, 'values': _values}

    @_('para TEXTLINE',
        'empty')
    def para(self, p):
        if len(p) == 1:
            return ''
        else:
            return f"{p.para} {p.TEXTLINE.strip()}"

    @_('NEWLINE')
    def newlines(self, p):
        return None

    @_('newlines',
        'empty')
    def maybe_newlines(self, p):
        return None

    @_('')
    def empty(self, p):
        return None

    def error(self, p):
        self.isError = True
        print('ERROR: ', p)
        return None


class MDVocab(MDProperty):
    # debugfile = 'parser.out'
    log = MyLogger(sys.stderr)
    tokens = MDLexer.tokens
    isError = False

    @_('maybe_newlines name summary description metadata entries')
    def document(self, p):
        if self.isError:
            return None
        return SpecVocab(p.name, p.summary, p.description, p.metadata, p.entries)

    @_('H1 TEXTLINE')
    def name(self, p):
        return p.TEXTLINE.strip()

    @_('SUMMARY para',
        'empty')
    def summary(self, p):
        if len(p) == 1:
            return None
        return p.para

    @_('DESCRIPTION para',
        'empty')
    def description(self, p):
        if len(p) == 1:
            return None
        return p.para

    @_('METADATA metadata_list',
        'empty')
    def metadata(self, p):
        if len(p) == 1:
            return []
        return p.metadata_list

    @_('metadata_list metadata_line',
        'empty')
    def metadata_list(self, p):
        if len(p) == 2:
            return p.metadata_list+[p.metadata_line]
        return []

    @_('ULISTA')
    def metadata_line(self, p):
        
        ulista = p.ULISTA

        # strip the md list identifier, ie r'[-*+]'
        ulista = re.split(r'[-*+]', ulista, 1)[-1].strip()

        # strip the key and value in metadata entry, ie. <key>: <value>
        ulista = re.split(r'\s*:\s', ulista, 1)

        if len(ulista) != 2:
            # report the invalid syntax
            self.error(p._slice[0])
            return None

        _key = ulista[0].strip()
        _values = re.split(r'\s',ulista[-1].strip())

        return {'name': _key, 'values': _values}

    @_('ENTRIES entry_list',
       'empty')
    def entries(self, p):
        if len(p) == 1:
            return []
        return p.entry_list

    @_('entry_list entry_line',
        'empty')
    def entry_list(self, p):
        if len(p) == 2:
            return p.entry_list+[p.entry_line]
        return []

    @_('ULISTA')
    def entry_line(self, p):
        
        ulista = p.ULISTA

        # strip the md list identifier, ie r'[-*+]'
        ulista = re.split(r'[-*+]', ulista, 1)[-1].strip()

        # strip the key and value in metadata entry, ie. <key>: <value>
        ulista = re.split(r'\s*:\s', ulista, 1)

        if len(ulista) != 2:
            # report the invalid syntax
            self.error(p._slice[0])
            return None

        _key = ulista[0].strip()
        _value = ulista[-1].strip()

        return {'name': _key, 'value': _value}

    @_('para TEXTLINE',
        'empty')
    def para(self, p):
        if len(p) == 1:
            return ''
        else:
            return f"{p.para} {p.TEXTLINE.strip()}"

    @_('NEWLINE')
    def newlines(self, p):
        return None

    @_('newlines',
        'empty')
    def maybe_newlines(self, p):
        return None

    @_('')
    def empty(self, p):
        return None

    def error(self, p):
        self.isError = True
        print('ERROR: ', p)
        return None



if __name__ == '__main__':

    lexer = MDLexer()
    parser = MDVocab()

    # fpath = sys.argv[1]
    fpath = "spec-v3-template/model/Core/Vocabularies/HashAlgorithmVocab.md"

    with open(fpath, "r") as f:
        inp = f.read()

    for tok in lexer.tokenize(inp):
        print(tok)

    result = parser.parse(lexer.tokenize(inp))
    result.dump_md('./test.md')
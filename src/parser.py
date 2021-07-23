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


class MDLexerList(Lexer):
    tokens = {
        WORD,
        COLON,
        NEWLINE
    }

    WORD = r'[^\s]*[^\s:]'
    COLON = r'\s*:\s'

    @_(r'\n+')
    def NEWLINE(self, t):
        self.lineno += len(t.value)
        self.pop_state()
        return t

    ignore_whitespace = r'\s+'


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
        DATAPROP,
        ENTRIES,
        WORD,
        COLON,
        TEXTLINE,
        ULISTA_INIT,
        ULISTB_INIT,
        ULISTA,
        ULISTB,
        NEWLINE,
    }

    SUMMARY = r'((?<=\n)|^)\#{2}\s+Summary\s+(\n+|$)'
    DESCRIPTION = r'((?<=\n)|^)\#{2}\s+Description\s+(\n+|$)'
    METADATA = r'((?<=\n)|^)\#{2}\s+Metadata\s+(\n+|$)'
    DATAPROP = r'((?<=\n)|^)\#{2}\s+Properties\s+(\n+|$)'
    ENTRIES = r'((?<=\n)|^)\#{2}\s+Entries\s+(\n+|$)'

    H6 = r'((?<=\n)|^)\#{6}'
    H5 = r'((?<=\n)|^)\#{5}'
    H4 = r'((?<=\n)|^)\#{4}'
    H3 = r'((?<=\n)|^)\#{3}'
    H2 = r'((?<=\n)|^)\#{2}'
    H1 = r'((?<=\n)|^)\#{1}'

    @_(r'((?<=\n)|^)[*+-]')
    def ULISTA_INIT(self, t):
        self.push_state(MDLexerList)
        return t

    @_(r'((?<=\n)|^)([ ]{2,4}|\t)[*+-]')
    def ULISTB_INIT(self, t):
        self.push_state(MDLexerList)
        return t


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

    @_('maybe_newlines name summary description metadata properties')
    def document(self, p):
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

    @_('ULISTA_INIT word COLON word_list')
    def metadata_line(self, p):
        return {'name': p.word, 'values': p.word_list}

    @_('DATAPROP entries',
        'empty')
    def properties(self, p):
        if len(p) == 1:
            return []
        return p.entries

    @_('entries entry',
        'empty')
    def entries(self, p):
        if len(p) == 1:
            return []
        return p.entries+[p.entry]

    @_('ULISTA_INIT word avline_list')
    def entry(self, p):
        return {'name': p.word, 'values': p.avline_list}

    @_('avline_list avline',
        'avline')
    def avline_list(self, p):
        if len(p) == 1:
            return [p.avline]
        return p.avline_list + [p.avline]

    @_('ULISTB_INIT word COLON word_list')
    def avline(self, p):
        return {'name': p.word, 'values': p.word_list}

    @_('WORD NEWLINE',
        'WORD')
    def word(self, p):
        return p.WORD.strip()

    @_('word_list word',
        'word')
    def word_list(self, p):
        if len(p) == 1:
            return [p.word]
        return p.word_list + [p.word]

    @_('para TEXTLINE',
        'empty')
    def para(self, p):
        if len(p) == 1:
            return ''
        else:
            return f"{p.para} {p.TEXTLINE}".strip()

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
        print('ERROR: ', p)
        return None


class MDProperty(Parser):

    # debugfile = 'parser.out'
    log = MyLogger(sys.stderr)
    tokens = MDLexer.tokens

    @_('maybe_newlines name summary description metadata')
    def document(self, p):
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

    @_('ULISTA_INIT word COLON word_list')
    def metadata_line(self, p):
        return {'name': p.word, 'values': p.word_list}
        
    @_('WORD NEWLINE',
        'WORD')
    def word(self, p):
        return p.WORD.strip()

    @_('word_list word',
        'word')
    def word_list(self, p):
        if len(p) == 1:
            return [p.word]
        return p.word_list + [p.word]

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
        print('ERROR: ', p)
        return None


class MDVocab(Parser):

    # debugfile = 'parser.out'
    log = MyLogger(sys.stderr)
    tokens = MDLexer.tokens

    @_('maybe_newlines name summary description metadata entries')
    def document(self, p):
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

    @_('ULISTA_INIT word COLON word_list')
    def metadata_line(self, p):
        return {'name': p.word, 'values': p.word_list}

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

    @_('ULISTA_INIT word COLON word_list')
    def entry_line(self, p):
        return {'name': p.word, 'values': p.word_list}

    @_('WORD NEWLINE',
        'WORD')
    def word(self, p):
        return p.WORD.strip()

    @_('word_list word',
        'word')
    def word_list(self, p):
        if len(p) == 1:
            return [p.word]
        return p.word_list + [p.word]

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
        print('ERROR: ', p)
        return None


if __name__ == '__main__':

    lexer = MDLexer()
    parser = MDVocab()

    with open(sys.argv[1], "r") as f:
        inp = f.read()

    for tok in lexer.tokenize(inp):
        print(tok)

    result = parser.parse(lexer.tokenize(inp))
    result.dump_md('./test.md')

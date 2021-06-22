import re
import sys
import textwrap
from sly import Lexer


class MDLexer(Lexer):

    tokens = {
        HEADLINE,
        TOPHEADLINE,
        DESCRIPTION,
        METADATA,
        DATAPROP,
        INSTANCES,
        TEXTLINE,
        ULISTA,
        ULISTB,
        NEWLINE,
    }

    @_(r'((?<=\n)|^)\#{1,6}\s+[^`*\n\t#\\[\]]+(\n+|$)')
    def HEADLINE(self, t):
        if m := re.fullmatch(r'(?P<hN>\#{1,6})\s+(?P<title>[^`*\n\t#\\[\]]+)(\n+|$)', t.value):
            t.value = (m.group('hN'), m.group('title'))
            if t.value[0] == '#':
                t.type = 'TOPHEADLINE'
            if t.value == ('##', 'Description'):
                t.type = 'DESCRIPTION'
            elif t.value == ('##', 'Metadata'):
                t.type = 'METADATA'
            elif t.value == ('##', 'Data Properties'):
                t.type = 'DATAPROP'
            elif t.value == ('##', 'Instances'):
                t.type = 'INSTANCES'
            return t
        self.error(t)

    @_(r'((?<=\n)|^)[*+-]\s+[^`*\n\t\\[\]]+(\n+|$)')
    def ULISTA(self, t):
        if m := re.fullmatch(r'[*+-]\s+(?P<text>[^`*\n\t\\[\]]+)(\n+|$)', t.value):
            t.value = m.group('text')
            return t
        self.error(t)

    @_(r'((?<=\n)|^)\s[*+-]\s+[^`*\n\t\\[\]]+(\n+|$)')
    def ULISTB(self, t):
        if m := re.fullmatch(r'\s[*+-]\s+(?P<text>[^`*\n\t\\[\]]+)(\n+|$)', t.value):
            t.value = m.group('text')
            return t
        self.error(t)

    @_(r'[^`*\n\t\\[\]]+(\n+|$)')
    def TEXTLINE(self, t):
        if m := re.fullmatch(r'(?P<text>[^`*\n\t\\[\]]+)(\n+|$)', t.value):
            t.value = m.group('text')
            return t
        self.error(t)

    ignore_comment = r'<!?--(?:(?!-->)(.|\n|\s))*-->\n*'

    @_(r'\n+$')
    def NEWLINE(self, t):
        self.lineno += len(t.value)
        return t

    def error(self, t):
        print("Illegal character '%s'" % t.value[0])
        self.index += 1


if __name__ == "__main__":
    with open(sys.argv[1], "r") as f:
        inp = f.read()

    lex = MDLexer()
    for tok in lex.tokenize(inp):
        print(tok)

import sys
from sly import Parser
from lexer import MDLexer


class MDParser(Parser):

    # debugfile = 'parser.out'
    tokens = MDLexer.tokens

    @_('TOPHEADLINE description')
    def document(self, p):
        return ['document', p.TOPHEADLINE, p.description]

    @_('empty')
    def description(self, p):
        return ['description']

    @_('DESCRIPTION TEXTLINE')
    def description(self, p):
        return ['description', p.TEXTLINE]

    @_('')
    def empty(self, p):
        return None

    def error(self, p):
        print('ERROR: ', p)
        return None


if __name__ == '__main__':
    lexer = MDLexer()
    parser = MDParser()

    with open(sys.argv[1], "r") as f:
        inp = f.read()

    result = parser.parse(lexer.tokenize(inp))
    print(result)

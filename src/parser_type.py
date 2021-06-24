import sys
from sly import Parser
from lexer import MDLexer


class MDParser(Parser):

    # debugfile = 'parser.out'
    tokens = MDLexer.tokens

    @_('TOPHEADLINE description metadata instances')
    def document(self, p):
        return ['document', p.TOPHEADLINE, p.description, p.metadata, p.instances]

    @_('empty')
    def description(self, p):
        return ['description']

    @_('DESCRIPTION TEXTLINE')
    def description(self, p):
        return ['description', p.TEXTLINE]

    @_('empty')
    def metadata(self, p):
        return ['metadata']

    @_('METADATA ULISTA')
    def metadata(self, p):
        return ['metadata', p[1]]

    @_('empty')
    def instances(self, p):
        return ['instances']

    @_('INSTANCES specs')
    def instances(self, p):
        return ['instances', p.specs]

    @_('specs ULISTA')
    def specs(self, p):
        return p.specs+[p.ULISTA]

    @_('ULISTA')
    def specs(self, p):
        return [p.ULISTA]

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

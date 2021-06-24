import sys
from sly import Parser
from lexer import MDLexer


class MDParser(Parser):

    # debugfile = 'parser.out'
    tokens = MDLexer.tokens

    @_('TOPHEADLINE description metadata data_prop instances')
    def document(self, p):
        return ['document', p.TOPHEADLINE, p.description, p.metadata, p.data_prop]

    @_('empty')
    def description(self, p):
        return ['description']

    @_('DESCRIPTION TEXTLINE')
    def description(self, p):
        return ['description', p.TEXTLINE]

    @_('empty')
    def metadata(self, p):
        return ['metadata']

    @_('METADATA TEXTLINE',
        'METADATA ULISTA')
    def metadata(self, p):
        return ['metadata', p[1]]

    @_('empty')
    def data_prop(self, p):
        return ['data_prop']

    @_('DATAPROP data_types')
    def data_prop(self, p):
        return ['data_prop', p.data_types]

    @_('empty')
    def instances(self, p):
        return ['instances']

    @_('INSTANCES specs')
    def instances(self, p):
        return ['instances', p.specs]

    @_('specs spec')
    def specs(self, p):
        return p.specs+[p.spec]

    @_('spec')
    def specs(self, p):
        return [p.spec]

    @_('ULISTA')
    def spec(self, p):
        return p.ULISTA

    @_('data_types data_type')
    def data_types(self, p):
        return p.data_types+[p.data_type]

    @_('data_type')
    def data_types(self, p):
        return [p.data_type]

    @_('ULISTA props')
    def data_type(self, p):
        return [p.ULISTA, p.props]

    @_('props prop')
    def props(self, p):
        return p.props+[p.prop]

    @_('prop')
    def props(self, p):
        return p.prop

    @_('ULISTB')
    def prop(self, p):
        return p.ULISTB

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

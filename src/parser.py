import sys
from sly import Parser
from lexer import MDLexer


class MDParser(Parser):

    tokens = MDLexer.tokens

    @_('HEADLINE NEWLINE description metadata data_prop instances')
    def document(self, p):
        return ['document', p.HEADLINE, p.description, p.metadata, p.data_prop]

    @_('empty')
    def description(self, p):
        return ['description']

    @_('HEADLINE NEWLINE TEXTLINE',
        'HEADLINE NEWLINE TEXTLINE NEWLINE')
    def description(self, p):
        return ['description', p.HEADLINE, p.TEXTLINE]

    @_('empty')
    def metadata(self, p):
        return ['metadata']

    @_('HEADLINE NEWLINE TEXTLINE',
        'HEADLINE NEWLINE TEXTLINE NEWLINE')
    def metadata(self, p):
        return ['metadata', p.HEADLINE, p.TEXTLINE]

    @_('empty')
    def data_prop(self, p):
        return ['data_prop']

    @_('HEADLINE NEWLINE data_types',
        'HEADLINE NEWLINE data_types NEWLINE')
    def data_prop(self, p):
        return ['data_prop', p.HEADLINE, p.data_types]

    @_('data_types NEWLINE data_type')
    def data_types(self, p):
        return p.data_types+[p.data_type]

    @_('data_type')
    def data_types(self, p):
        return p.data_type

    @_('ULIST_ITEM_0 NEWLINE props',
        'ULIST_ITEM_0 NEWLINE props NEWLINE')
    def data_type(self, p):
        return [p.ULIST_ITEM_0, p.props]

    @_('props NEWLINE prop')
    def props(self, p):
        return p.props0+[p.prop]

    @_('prop')
    def props(self, p):
        return p.prop

    @_('ULIST_ITEM_1')
    def prop(self, p):
        return p.ULIST_ITEM_1

    # @_('INSTANCES NEWLINE ')

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

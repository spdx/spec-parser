from utils import *
import sys
import re
from sly import Parser, Lexer


class MDLexer(Lexer):

    tokens = {
        HASHES_1,
        HASHES_2,
        HASHES_3,
        HASHES_4,
        HASHES_5,
        HASHES_6,
        DESCRIPTION,
        METADATA,
        DATAPROP,
        INSTANCES,
        TEXTLINE,
        ULISTA,
        ULISTB,
        NEWLINE,
    }

    DESCRIPTION = r'((?<=\n)|^)\#{2}\s+Description\s+(\n+|$)'
    METADATA = r'((?<=\n)|^)\#{2}\s+Metadata\s+(\n+|$)'
    DATAPROP = r'((?<=\n)|^)\#{2}\s+Data Properties\s+(\n+|$)'
    INSTANCES = r'((?<=\n)|^)\#{2}\s+Instances\s+(\n+|$)'

    HASHES_6 = r'((?<=\n)|^)\#{6}'
    HASHES_5 = r'((?<=\n)|^)\#{5}'
    HASHES_4 = r'((?<=\n)|^)\#{4}'
    HASHES_3 = r'((?<=\n)|^)\#{3}'
    HASHES_2 = r'((?<=\n)|^)\#{2}'
    HASHES_1 = r'((?<=\n)|^)\#{1}'

    ULISTA = r'((?<=\n)|^)[*+-][^`*\n\t\\[\]]+(\n+|$)'
    ULISTB = r'((?<=\n)|^)([ ]{2,4}|\t)[*+-][^`*\n\t\\[\]]+(\n+|$)'

    TEXTLINE = r'[^`*\n\t\\[\]]+(\n+|$)'

    ignore_comment = r'<!?--(?:(?!-->)(.|\n|\s))*-->\n*'

    @_(r'\n+$')
    def NEWLINE(self, t):
        self.lineno += len(t.value)
        return t

    def error(self, t):
        print("Illegal character '%s'" % t.value[0])
        self.index += 1


class MDElement(Parser):

    # debugfile = 'parser.out'
    tokens = MDLexer.tokens

    @_('topheadline description metadata data_prop')
    def document(self, p):
        return SpecElement(p.topheadline, p.description, p.metadata, p.data_prop)

    @_('HASHES_1 TEXTLINE')
    def topheadline(self, p):
        return p.TEXTLINE.strip()

    @_('empty')
    def description(self, p):
        return p.empty

    @_('DESCRIPTION para')
    def description(self, p):
        return p.para

    @_('empty')
    def metadata(self, p):
        return None

    @_('METADATA para')
    def metadata(self, p):
        return p.para

    @_('empty')
    def data_prop(self, p):
        return []

    @ _('DATAPROP props')
    def data_prop(self, p):
        return p.props

    @ _('props prop')
    def props(self, p):
        return p.props+[p.prop]

    @ _('prop')
    def props(self, p):
        return [p.prop]

    @ _('ULISTA subprops')
    def prop(self, p):
        # TODO: do preprocessing if needed
        return {'name': p.ULISTA.strip(), 'subprops': p.subprops}

    @ _('subprops subprop',
        'subprop')
    def subprops(self, p):
        if len(p) == 2:
            return p.subprops + [p.subprop]
        else:
            return [p.subprop]

    @ _('ULISTB')
    def subprop(self, p):
        # TODO: do preprocessing if needed
        return p.ULISTB.strip()

    @ _('para TEXTLINE',
        'TEXTLINE')
    def para(self, p):
        if len(p) == 1:
            return p.TEXTLINE.strip()
        else:
            return ' '.join([p.para, p.TEXTLINE.strip()])

    @ _('')
    def empty(self, p):
        return None

    def error(self, p):
        print('ERROR: ', p)
        return None


class MDType(Parser):

    # debugfile = 'parser.out'
    tokens = MDLexer.tokens

    @ _('topheadline description metadata instances')
    def document(self, p):
        return SpecType(p.topheadline, p.description, p.metadata, p.instances)

    @ _('HASHES_1 TEXTLINE')
    def topheadline(self, p):
        return p.TEXTLINE.strip()

    @ _('empty')
    def description(self, p):
        return p.empty

    @ _('DESCRIPTION para')
    def description(self, p):
        return p.para

    @ _('empty')
    def metadata(self, p):
        return None

    @ _('METADATA ULISTA')
    def metadata(self, p):
        return p.ULISTA.strip()

    @ _('empty')
    def instances(self, p):
        return []

    @ _('INSTANCES instances_list')
    def instances(self, p):
        return p.instances_list

    @ _('instances_list ULISTA',
        'ULISTA')
    def instances_list(self, p):
        if len(p) == 2:
            return p.instances_list + [p.ULISTA.strip()]
        else:
            return [p.ULISTA.strip()]

    @ _('para TEXTLINE',
        'TEXTLINE')
    def para(self, p):
        if len(p) == 1:
            return p.TEXTLINE.strip()
        else:
            return ' '.join([p.para, p.TEXTLINE.strip()])

    @ _('')
    def empty(self, p):
        return None

    def error(self, p):
        print('ERROR: ', p)
        return None


class MDProperty(Parser):

    # debugfile = 'parser.out'
    tokens = MDLexer.tokens

    @ _('properties')
    def document(self, p):
        return SpecProperty(p.properties)

    @ _('properties property',
        'property')
    def properties(self, p):
        if len(p) == 2:
            return p.properties + [p.property]
        else:
            return [p.property]

    @ _('topheadline description metadata')
    def property(self, p):
        return {'name': p.topheadline, 'description': p.description, 'metadata': p.metadata}

    @ _('HASHES_1 TEXTLINE')
    def topheadline(self, p):
        return p.TEXTLINE.strip()

    @ _('DESCRIPTION para')
    def description(self, p):
        return p.para

    @ _('METADATA prop_relations')
    def metadata(self, p):
        return p.prop_relations

    @ _('prop_relations ULISTA',
        'ULISTA')
    def prop_relations(self, p):
        if len(p) == 2:
            return p.prop_relations + [p.ULISTA.strip()]
        else:
            return [p.ULISTA.strip()]

    @ _('para TEXTLINE',
        'TEXTLINE')
    def para(self, p):
        if len(p) == 1:
            return p.TEXTLINE.strip()
        else:
            return ' '.join([p.para, p.TEXTLINE.strip()])

    @ _('')
    def empty(self, p):
        return None

    def error(self, p):
        print('ERROR: ', p)
        return None


class MDProfile(Parser):

    # debugfile = 'parser.out'
    tokens = MDLexer.tokens

    @ _('topheadline description')
    def document(self, p):
        return SpecProfile(p.topheadline, p.description)

    @ _('HASHES_1 TEXTLINE')
    def topheadline(self, p):
        return p.TEXTLINE.strip()

    @ _('empty')
    def description(self, p):
        return p.empty

    @ _('DESCRIPTION para')
    def description(self, p):
        return p.para

    @ _('para TEXTLINE',
        'TEXTLINE')
    def para(self, p):
        if len(p) == 1:
            return p.TEXTLINE.strip()
        else:
            return ' '.join([p.para, p.TEXTLINE.strip()])

    @ _('')
    def empty(self, p):
        return None

    def error(self, p):
        print('ERROR: ', p)
        return None


if __name__ == '__main__':

    lexer = MDLexer()
    parser = MDProfile()

    with open(sys.argv[1], "r") as f:
        inp = f.read()

    for tok in lexer.tokenize(inp):
        print(tok)

    result = parser.parse(lexer.tokenize(inp))
    result.dump_md('nirmal/test.md')
    print(result)

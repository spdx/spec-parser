import re
import sys
import textwrap
from sly import Lexer


class MDLexer(Lexer):

    tokens = {
        HEADLINE,
        TEXTLINE,
        ULIST_ITEM_0,
        ULIST_ITEM_1,
        NEWLINE,
    }

    HEADLINE = r'\#{1,6}\s[^`*\n\t#\\[\]]+'
    ULIST_ITEM_0 = r'[*+-]\s[^`*\n\t\\[\]]+'
    ULIST_ITEM_1 = r'\s[*+-]\s[^`*\n\t\\[\]]+'
    TEXTLINE = r'[^`*\n\t\\[\]]+'
    ignore_comment = r'<!?--(?:(?!-->)(.|\n|\s))*-->\n*'

    @_(r'\n+|\n$')
    def NEWLINE(self, t):
        self.lineno += len(t.value)
        return t


if __name__ == "__main__":
    with open(sys.argv[1], "r") as f:
        inp = f.read()

    lex = MDLexer()
    for tok in lex.tokenize(inp):
        print(tok)

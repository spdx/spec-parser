import os
import os.path as path
from parser import (
    MDClass,
    MDLexer,
    MDProperty,
    MDVocab
)
from helper import safe_listdir

from utils import *

__all__ = ['SpecParser']


class SpecParser:

    def __init__(self):

        # markdown parser
        self.lexer = MDLexer()
        self.mdClass = MDClass()
        self.mdProperty = MDProperty()
        self.mdVocab = MDVocab()

    def parse(self, spec_dir):

        # flag for error during parsing
        isError = False

        # init the Spec object for storing parsed information
        spec_obj = Spec(spec_dir)

        # traverse through all namespace and parse !!
        for namespace in safe_listdir(spec_dir):

            if not path.isdir(path.join(spec_dir, namespace)):
                continue

            classes = []
            properties = []
            vocabularies = []

            # parse all markdown files inside Classes folder
            classes_dir = path.join(spec_dir, namespace, 'Classes')
            for fname in safe_listdir(classes_dir):

                # Construct file path
                fname = path.join(classes_dir, fname)

                # if file is not markdown file then skip
                if not self.isMarkdown(fname):
                    continue

                # try parsing class markdown
                specClass = self.parse_class(fname)

                if specClass is None:
                    # set the error flag
                    isError = True
                else:
                    classes.append(specClass)

            # parse all markdown files inside Properties folder
            props_dir = path.join(spec_dir, namespace, 'Properties')
            for fname in safe_listdir(props_dir):

                # Construct file path
                fname = path.join(props_dir, fname)

                # if file is not markdown file then skip
                if not self.isMarkdown(fname):
                    continue

                # try parsing property markdown
                specProperty = self.parse_property(fname)

                if specProperty is None:
                    # set the error flag
                    isError = True
                else:
                    properties.append(specProperty)

            # parse all markdown files inside Vocabularies folder
            vocabs_dir = path.join(spec_dir, namespace, 'Vocabularies')
            for fname in safe_listdir(vocabs_dir):

                # Construct file path
                fname = path.join(vocabs_dir, fname)

                # if file is not markdown file then skip
                if not self.isMarkdown(fname):
                    continue

                # try parsing vacab markdown
                specVocab = self.parse_vocab(fname)

                if specVocab is None:
                    # set the error flag
                    isError = True
                else:
                    vocabularies.append(specVocab)

            # add the namespace in spec object
            spec_obj.add_namespace(
                namespace, classes, properties, vocabularies)

        # if we encounter error, then return None element
        if isError:
            return None

        return spec_obj

    def parse_class(self, fname: str):

        text = self.get_text(fname)
        if text is None:
            # report to logger and return
            return None

        specClass = self.mdClass.parse(self.lexer.tokenize(text))

        if specClass is None:
            print(fname)
            # report to logger and return
            return None

        return specClass

    def parse_property(self, fname: str):

        text = self.get_text(fname)
        if text is None:
            # report to logger and return
            return None

        specProperty = self.mdProperty.parse(self.lexer.tokenize(text))

        if specProperty is None:
            print(fname)
            # report to logger and return
            return None

        return specProperty

    def parse_vocab(self, fname: str):

        text = self.get_text(fname)
        if text is None:
            # report to logger and return
            return None

        specVocab = self.mdVocab.parse(self.lexer.tokenize(text))

        if specVocab is None:
            print(fname)
            # report to logger and return
            return None

        return specVocab

    def isMarkdown(self, fname):
        if path.isfile(fname) and fname.endswith('.md'):
            return True
        return False

    def get_text(self, fname):

        if not os.path.isfile(fname):
            return None

        with open(fname, "r") as f:
            inp = f.read()

        return inp

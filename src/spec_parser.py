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
import logging

logger = logging.getLogger(__name__)

__all__ = ['SpecParser']


class SpecParser:

    def __init__(self):

        # markdown parser
        self.lexer = MDLexer()
        self.mdClass = MDClass()
        self.mdProperty = MDProperty()
        self.mdVocab = MDVocab()
        self.logger = logging.getLogger(self.__class__.__name__)

    def parse(self, spec_dir):

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

                if specClass is not None:
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

                if specProperty is not None:
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

                if specVocab is not None:
                    vocabularies.append(specVocab)

            # add the namespace in spec object
            spec_obj.add_namespace(
                namespace, classes, properties, vocabularies)

        return spec_obj

    def parse_class(self, fname: str):

        text = self.get_text(fname)
        if text is None:
            return None

        specClass = self.mdClass.parse(self.lexer.tokenize(text))

        if specClass is None:
            self.logger.error(f'Unable to parse `Class` markdown: \'{fname}\'')
            return None

        return specClass

    def parse_property(self, fname: str):

        text = self.get_text(fname)
        if text is None:
            return None

        specProperty = self.mdProperty.parse(self.lexer.tokenize(text))

        if specProperty is None:
            print(fname)
            self.logger.error(f'Unable to parse `Property` markdown: \'{fname}\'')
            return None

        return specProperty

    def parse_vocab(self, fname: str):

        text = self.get_text(fname)
        if text is None:
            return None

        specVocab = self.mdVocab.parse(self.lexer.tokenize(text))

        if specVocab is None:
            self.logger.error(f'Unable to parse `Vocabulary` markdown: \'{fname}\'')
            return None

        return specVocab

    def isMarkdown(self, fname):
        if path.isfile(fname) and fname.endswith('.md'):
            return True
        return False

    def get_text(self, fname):

        if not os.path.isfile(fname):
            self.logger(f'No such file exists: \'{fname}\'')
            return None

        with open(fname, "r") as f:
            inp = f.read()

        return inp

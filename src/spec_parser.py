import os
import re
import os.path as path
from parser import (
    MDClass,
    MDLexer,
    MDProperty,
    MDVocab
)
from helper import safe_listdir
import logging
from utils import Spec, SpecClass, SpecProperty, SpecVocab

logger = logging.getLogger(__name__)
__all__ = ['SpecParser']


class SpecParser:

    def __init__(self):

        # markdown parser
        self.lexer = MDLexer()
        self.mdClass = MDClass()
        self.mdProperty = MDProperty()
        self.mdVocab = MDVocab()

        self.mdClass.lexer = self.lexer
        self.mdProperty.lexer = self.lexer
        self.mdVocab.lexer = self.lexer

        self.logger = logging.getLogger(self.__class__.__name__)

    def parse(self, spec_dir):

        # init the Spec object for storing parsed information
        self.spec_obj = Spec(spec_dir)

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
                specClass = self.parse_class(fname, namespace)

                if specClass is None:
                    continue

                specClass.namespace_name = namespace
                specClass.spec = self
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
                specProperty = self.parse_property(fname, namespace)

                if specProperty is None:
                    continue

                specProperty.namespace_name = namespace
                specProperty.spec = self
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
                specVocab = self.parse_vocab(fname, namespace)

                if specVocab is None:
                    continue

                specVocab.namespace_name = namespace
                specVocab.spec = self
                vocabularies.append(specVocab)

            # add the namespace in spec object
            self.spec_obj.add_namespace(
                namespace, classes, properties, vocabularies)

        return self.spec_obj

    def parse_class(self, fname: str, namespace: str):

        text = self.get_text(fname)
        if text is None:
            return None

        self.lexer.fname = fname
        self.mdClass.fname = fname
        self.mdClass.text = text

        parsed = self.mdClass.parse(self.lexer.tokenize(text))

        if parsed is None:
            self.logger.error(f'Unable to parse `Class` markdown: \'{fname}\'')
            return None

        specClass = SpecClass(self.spec_obj, namespace, *parsed)
        return specClass

    def parse_property(self, fname: str, namespace: str):

        text = self.get_text(fname)
        if text is None:
            return None

        self.lexer.fname = fname
        self.mdProperty.fname = fname
        self.mdProperty.text = text

        parsed = self.mdProperty.parse(self.lexer.tokenize(text))

        if parsed is None:
            print(fname)
            self.logger.error(
                f'Unable to parse `Property` markdown: \'{fname}\'')
            return None

        specProperty = SpecProperty(self.spec_obj, namespace, *parsed)
        return specProperty

    def parse_vocab(self, fname: str, namespace: str):

        text = self.get_text(fname)
        if text is None:
            return None

        self.lexer.fname = fname
        self.mdVocab.fname = fname
        self.mdVocab.text = text
        parsed = self.mdVocab.parse(self.lexer.tokenize(text))

        if parsed is None:
            self.logger.error(
                f'Unable to parse `Vocabulary` markdown: \'{fname}\'')
            return None

        specVocab = SpecVocab(self.spec_obj, namespace, *parsed)
        return specVocab

    def isMarkdown(self, fname):

        if not path.isfile(fname) or not fname.endswith('.md'):
            return False

        if m := re.match(r'^_(\w*).md$', path.split(fname)[-1]):
            self.logger.warning(f'skipping {fname}')
            return False

        return True

    def get_text(self, fname):

        if not os.path.isfile(fname):
            self.logger(f'No such file exists: \'{fname}\'')
            return None

        with open(fname, "r") as f:
            inp = f.read()

        return inp

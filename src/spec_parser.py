import os
import os.path as path
from parser import MDLexer, MDElement, MDType, MDProfile

from utils import *

__all__ = ['SpecParser']


class SpecParser:

    def __init__(self):

        # parser related utils
        self.lexer = MDLexer()
        self.mdClass = MDElement()
        self.mdType = MDType()
        self.mdProfile = MDProfile()

        # class for storing to Models and Profile
        self.model = None
        self.profile = None

    def parse(self, model, profile, dump_md, out_dir):

        # find all namespaces by scanning model directory
        namespaces = [n for n in os.listdir(
            model) if path.isdir(path.join(model, n))]

        spec_obj = Spec(model, profile)
        for namespace in namespaces:

            # parse all elements present inside namespace
            self.parse_namespace(namespace, path.join(
                model, namespace), spec_obj)

            # parse profile of namespace
            profile_path = os.join(profile, namespace+'.md')
            self.parse_profile(profile_path, spec_obj)

        # if we need to dump the result markdown
        if dump_md:
            spec_obj.dump_md(out_dir)

    def isElement(fname):
        if fname.endswith('.md') and not fname.endswith('Type.md'):
            return True
        return False

    def parse_namespace(self, name, dname, obj):

        namespace_obj = SpecNamespace(name)

        for fname in os.listdir(dname):
            if self.isElement(fname):
                element = self.parse_element(fname)

        obj.add_namespace(namespace_obj)

    def parse_element(self, fname, obj):

        if not os.path.isfile(fname):
            # report the error to logger
            return

        text = self.get_text(fname)
        specElement = None
        if text is None:
            # report to logger and return
            return

        specElement = self.MDClass.parse(self.lexer.tokenize(text))

        if specElement is None:
            # report to logger and return
            return

        obj.add_element(specElement)

    def parse_type(self, fname):
        pass

    def parse_profile(self, fname, obj):

        if not os.path.isfile(fname):
            # report the error to logger
            return

        text = self.get_text(fname)
        specProfile = None
        if text is None:
            # report to logger and return
            return

        specProfile = self.mdProfile.parse(self.lexer.tokenize(text))

        if specProfile is None:
            # report to logger and return
            return

        obj.add_element(specProfile)

    def get_text(self, name):

        if not os.path.isfile(name):
            return None

        with open(name, "r") as f:
            inp = f.read()

        return inp
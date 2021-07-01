import os
import os.path as path
from parser import *

from utils import *

__all__ = ['SpecParser']


class SpecParser:

    def __init__(self):

        # parser related utils
        self.lexer = MDLexer()
        self.mdClass = MDElement()
        self.mdType = MDType()
        self.mdProperty = MDProperty()
        self.mdProfile = MDProfile()

    def parse(self, model_dir, profile_dir, dump_md, out_dir):

        # find all namespaces by scanning model directory
        namespaces = [n for n in os.listdir(
            model_dir) if path.isdir(path.join(model_dir, n))]

        spec_obj = Spec(model_dir, profile_dir)
        for namespace in namespaces:
            # parse all elements present inside namespace
            self.parse_namespace(namespace, path.join(
                model_dir, namespace), spec_obj)

        profiles = [n for n in os.listdir(
            profile_dir) if path.isfile(path.join(profile_dir, n))]

        for profile in profiles:
            # parse profile of namespace
            profile_path = os.path.join(profile_dir, profile)
            self.parse_profile(profile_path, spec_obj)

        # if we need to dump the result markdown
        # if dump_md:
        #     spec_obj.dump_md(out_dir)

        return spec_obj

    def isElement(self, fname):
        if fname.endswith('.md') and not fname.endswith('Type.md') \
                and not fname.endswith('properties.md'):
            return True
        return False

    def isType(self, fname):
        if fname.endswith('Type.md'):
            return True
        return False

    def isProperty(self, fname):
        if fname.endswith('properties.md'):
            return True
        return False

    def parse_namespace(self, name, dir, obj):

        namespace_obj = SpecNamespace(name)

        for fname in os.listdir(dir):
            path = os.path.join(dir, fname)
            if self.isElement(fname):
                self.parse_element(path, namespace_obj)
            elif self.isType(fname):
                self.parse_type(path, namespace_obj)
            elif self.isProperty(fname):
                self.parse_property(path, namespace_obj)
            else:
                # report the error and move forward
                pass

        obj.add_namespace(namespace_obj)

    def parse_element(self, path, obj):

        text = self.get_text(path)
        specElement = None
        if text is None:
            # report to logger and return
            return

        specElement = self.mdClass.parse(self.lexer.tokenize(text))

        if specElement is None:
            print(path)
            # report to logger and return
            return

        obj.add_element(specElement)

    def parse_type(self, path, obj):

        text = self.get_text(path)
        if text is None:
            # report to logger and return
            return

        specType = self.mdType.parse(self.lexer.tokenize(text))

        if specType is None:
            # report to logger and return
            return

        obj.add_type(specType)

    def parse_property(self, path, obj):

        text = self.get_text(path)
        if text is None:
            # report to logger and return
            return

        specProperty = self.mdProperty.parse(self.lexer.tokenize(text))

        if specProperty is None:
            # report to logger and return
            return

        obj.add_property(specProperty)

    def parse_profile(self, path, obj):

        text = self.get_text(path)
        if text is None:
            # report to logger and return
            return

        specProfile = self.mdProfile.parse(self.lexer.tokenize(text))

        if specProfile is None:
            # report to logger and return
            return

        obj.add_profile(specProfile)

    def get_text(self, name):

        if not os.path.isfile(name):
            return None

        with open(name, "r") as f:
            inp = f.read()

        return inp

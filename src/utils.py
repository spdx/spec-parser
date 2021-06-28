from helper import safe_open
from __version__ import __version__


class Spec:
    def __init__(self, model_dir, profile_dir):

        self.model_dir = model_dir
        self.profile_dir = profile_dir
        self.namespaces = {}
        self.profiles = {}

    def add_namespace(self, namespace):

        name = namespace.name

        if name in self.namespaces:
            # raiseError(f'ERROR: Namespace with name: {name} already exists')
            pass

        self.namespaces[name] = namespace

    def add_profile(self, profile):

        name = profile.name

        if name in self.profiles:
            # raiseError(f'ERROR: profile with name: {name} already exists')
            pass

        self.profiles[name] = profile


class SpecProfile:

    def __init__(self, name, description):
        self.name = name
        self.description = description


class SpecNamespace:

    def __init__(self, name):

        self.name = name

    def add_element(self, element):
        name = element.name

        if name in self.elements:
            # raiseError(f"ERROR: Element with name: {name} already exists")
            pass

        self.elements[name] = element


class SpecElement:

    def __init__(self, name, description, metadata, props):

        self.name = name
        self.description = description
        self.metadata = metadata
        self.properties = {}

        for prop in props:
            self.add_property(prop)

    def add_property(self, prop):

        name = prop['name']
        subprops = prop['subprops']

        if name in self.properties:
            # raiseError(
            #     f"ERROR: Data Property with name: {name} already exists")
            pass

        self.properties[name] = subprops

    def dump_md(self, fname):

        with safe_open(fname, 'w') as f:

            # write the header
            f.write(
                f'<!-- Auto generated markdown by Spec-parser {__version__} -->\n\n')

            # write the topheadline
            f.write(f'# {self.name}\n\n')

            if self.description is not None:
                # write the description
                f.write(f'## Description\n\n')
                f.write(f'{self.description}\n')
                f.write(f'\n')

            if self.metadata is not None:
                # write the metadata
                f.write(f'## Metadata\n\n')
                f.write(f'{self.metadata}\n\n')

            if len(self.properties) > 0:
                # write the data_props
                f.write(f'## Data Properties\n\n')
                for name, subprops in self.properties.items():
                    f.write(f'{name}\n')
                    for subprop in subprops:
                        f.write(f'\t{subprop}\n')

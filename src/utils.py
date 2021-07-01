import os
from helper import safe_open
from __version__ import __version__


class Spec:
    def __init__(self, model_dir, profile_dir):

        self.model_dir = model_dir
        self.profile_dir = profile_dir
        self.namespaces = dict()
        self.profiles = dict()

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

    def dump_md(self, out_dir):

        for name, namespace in self.namespaces.items():
            namespace.dump_md(os.path.join(out_dir, 'model', f'{name}'))

        for name, profile in self.profiles.items():
            profile.dump_md(os.path.join(out_dir, 'profiles', f'{name}.md'))


class SpecNamespace:

    def __init__(self, name):

        self.name = name
        self.elements = dict()
        self.types = dict()
        self.property = None

    def add_element(self, element):
        name = element.name

        if name in self.elements:
            # raiseError(f"ERROR: Element with name: {name} already exists")
            pass

        self.elements[name] = element

    def add_type(self, type):
        name = type.name

        if name in self.types:
            # raiseError(f"ERROR: type with name: {name} already exists")
            pass

        self.types[name] = type

    def add_property(self, property):
        if self.property is not None:
            # raiseError(f"ERROR: property with name: {name} already exists")
            pass

        self.property = property

    def dump_md(self, dir):

        # print(f'{self.name}\n\t{self.elements}\n\t{self.types}\n\t{self.property}')
        # return
        for name, element in self.elements.items():
            element.dump_md(os.path.join(dir, f'{name}.md'))

        for name, _type in self.types.items():
            _type.dump_md(os.path.join(dir, f'{name}.md'))

        if self.property:
            self.property.dump_md(os.path.join(dir, f'properties.md'))


class SpecProfile:

    def __init__(self, name, description):
        self.name = name
        self.description = description

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


class SpecType:

    def __init__(self, name, description, metadata, instances):

        self.name = name
        self.description = description
        self.metadata = metadata
        self.instances = set()

        for instance in instances:
            self.add_instance(instance)

    def add_instance(self, instance):

        if instance in self.instances:
            # raiseError(
            #     f"ERROR: Data Property with name: {name} already exists")
            pass

        self.instances.add(instance)

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

            if len(self.instances) > 0:
                # write the data_props
                f.write(f'## Instances\n\n')
                for instance in self.instances:
                    f.write(f'{instance}\n')


class SpecProperty:

    def __init__(self, properties):

        self.properties = dict()

        for property in properties:
            self.add_property(property)

    def add_property(self, property):

        name = property['name']

        if name in self.properties:
            # raiseError(
            #     f"ERROR: Data Property with name: {name} already exists")
            pass

        self.properties[name] = property

    def dump_md(self, fname):

        with safe_open(fname, 'w') as f:

            # write the header
            f.write(
                f'<!-- Auto generated markdown by Spec-parser {__version__} -->\n\n')

            # write the data_props
            for name, property in self.properties.items():

                description = property['description']
                metadata = property['metadata']

                # write the topheadline
                f.write(f'# {name}\n\n')

                if description is not None:
                    # write the description
                    f.write(f'## Description\n\n')
                    f.write(f'{description}\n')
                    f.write(f'\n')

                if metadata is not None:
                    # write the metadata
                    f.write(f'## Metadata\n\n')
                    for prop_relation in metadata:
                        f.write(f'{prop_relation}\n')
                    f.write('\n')


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

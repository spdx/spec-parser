import os
import logging
import re
from os import path
from helper import (
    isError,
    safe_open, 
    union_dict, 
    metadata_defaults,
    property_defaults
)
from __version__ import __version__


class Spec:
    def __init__(self, spec_dir):

        self.spec_dir = spec_dir
        self.namespaces = dict()
        self.logger = logging.getLogger(self.__class__.__name__)

    def add_namespace(self, name, classes, properties, vocabs):

        class_dict = dict()
        props_dict = dict()
        vocabs_dict = dict()

        for _class in classes:
            if _class.name in class_dict:
                # report error
                self.logger.error('Duplicate `Class` object found: \'{name}:{_class.name}\'')

            class_dict[_class.name] = _class

        for _prop in properties:
            if _prop.name in props_dict:
                # report error
                self.logger.error('Duplicate `Property` object found: \'{name}:{_prop.name}\'')

            props_dict[_prop.name] = _prop

        for _vocab in vocabs:
            if _vocab.name in vocabs_dict:
                # report error
                self.logger.error('Duplicate `Vocab` object found: \'{name}:{_vocab.name}\'')

            vocabs_dict[_vocab.name] = _vocab

        namespace_el = {'name': name, 'classes': class_dict,
                        'properties': props_dict, 'vocabs': vocabs_dict}

        if name in self.namespaces:
            self.logger.error(f'Namespace with name: {name} already exists')

        self.namespaces[name] = namespace_el

    def dump_md(self, out_dir):

        # if we have encounter error then terminate
        if isError():
            self.logger.warning(f'Error parsing the spec. Aborting the dump_md...')
            return

        for namespace_name, namespace in self.namespaces.items():

            classes = namespace['classes']
            properties = namespace['properties']
            vocabs = namespace['vocabs']

            for name, class_obj in classes.items():
                class_obj.dump_md(
                    path.join(out_dir, namespace_name, 'Classes', f'{name}.md'))

            for name, prop_obj in properties.items():
                prop_obj.dump_md(
                    path.join(out_dir, namespace_name, 'Properties', f'{name}.md'))

            for name, vocab_obj in vocabs.items():
                vocab_obj.dump_md(
                    path.join(out_dir, namespace_name, 'Vocabularies', f'{name}.md'))


class SpecClass:

    def __init__(self, name, summary, description, metadata, props):

        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = name
        self.summary = summary
        self.description = description

        self.metadata = dict()
        self.properties = dict()

        self.extract_metadata(metadata)

        # add all default metadata fields
        union_dict(self.metadata, metadata_defaults)

        self.extract_properties(props)

        # add all default property fields
        for val in self.properties.values():
            union_dict(val, property_defaults)

    def extract_metadata(self, mdata_list):

        for _dict in mdata_list:
            
            _key = _dict['name']
            _values = _dict['values']

            if _key in self.metadata:
                # report the error
                self.logger.error(f'{self.name}: Metadata key \'{_key}\' already exists')
            
            self.metadata[_key] = _values

    def extract_properties(self, props_list):

        for prop in props_list:

            name = prop['name']
            avline_list = prop['values']

            subprops_dict = dict()

            for avline in avline_list:

                _key = avline['name']
                _values = avline['values']

                if _key in subprops_dict:
                    # report the error
                    self.logger.error(f'{self.name}: Attribute key \'{_key}\' already exists in data property \'{name}\'')

                subprops_dict[_key] = _values

            if name in self.properties:
                # report the error
                self.logger.error(f'{self.name}: Data property \'{_key}\' already exists')

            self.properties[name] = subprops_dict

    def dump_md(self, fname):

        with safe_open(fname, 'w') as f:

            # write the header
            f.write(
                f'<!-- Auto generated markdown by Spec-parser v{__version__} -->\n\n')

            # write the topheadline
            f.write(f'# {self.name}\n\n')

            if self.summary is not None:
                # write the summary
                f.write(f'## Summary\n\n')
                f.write(f'{self.summary}\n')
                f.write(f'\n')

            if self.description is not None:
                # write the description
                f.write(f'## Description\n\n')
                f.write(f'{self.description}\n')
                f.write(f'\n')

            # write the metadata
            f.write(f'## Metadata\n\n')
            for name, vals in self.metadata.items():
                f.write(f'- {name}: {" ".join(vals)}\n')
            f.write('\n')

            # write the data_props
            f.write(f'## Properties\n\n')
            for name, subprops in self.properties.items():
                f.write(f'- {name}\n')
                for _key, subprop in subprops.items():
                    f.write(f'  - {_key}: {" ".join(subprop)}\n')
                f.write('\n')


class SpecProperty:

    def __init__(self, name, summary, description, metadata):

        self.name = name
        self.summary = summary
        self.description = description

        self.metadata = dict()

        self.extract_metadata(metadata)

        # add all default metadata fields
        union_dict(self.metadata, metadata_defaults)

    def extract_metadata(self, mdata_list):

        for mdata_line in mdata_list:

            _key = mdata_line['name']
            _values = mdata_line['values']

            if _key in self.metadata:
                # report the error
                self.logger.error(f'{self.name}: Metadata key \'{_key}\' already exists')

            self.metadata[_key] = _values

    def dump_md(self, fname):

        with safe_open(fname, 'w') as f:

            # write the header
            f.write(
                f'<!-- Auto generated markdown by Spec-parser v{__version__} -->\n\n')

            # write the topheadline
            f.write(f'# {self.name}\n\n')

            if self.summary is not None:
                # write the summary
                f.write(f'## Summary\n\n')
                f.write(f'{self.summary}\n')
                f.write(f'\n')

            if self.description is not None:
                # write the description
                f.write(f'## Description\n\n')
                f.write(f'{self.description}\n')
                f.write(f'\n')

            # write the metadata
            f.write(f'## Metadata\n\n')
            for name, val in self.metadata.items():
                f.write(f'- {name}: {" ".join(val)}\n')


class SpecVocab:

    def __init__(self, name, summary, description, metadata, entries):

        self.name = name
        self.summary = summary
        self.description = description

        self.metadata = dict()
        self.entries = dict()

        self.extract_metadata(metadata)

        # add all default metadata fields
        union_dict(self.metadata, metadata_defaults)

        self.extract_entries(entries)

    def extract_metadata(self, mdata_list):

        for mdata_line in mdata_list:

            _key = mdata_line['name']
            _values = mdata_line['values']

            if _key in self.metadata:
                # report the error
                self.logger.error(f'{self.name}: Metadata key \'{_key}\' already exists')

            self.metadata[_key] = _values

    def extract_entries(self, entry_list):

        for entry in entry_list:

            _key = entry['name']
            _value = entry['value']

            if _key in self.entries:
                # report the error
                self.logger.error(f'{self.name}: Entry \'{_key}\' already exists')

            self.entries[_key] = _value

    def dump_md(self, fname):

        with safe_open(fname, 'w') as f:

            # write the header
            f.write(
                f'<!-- Auto generated markdown by Spec-parser v{__version__} -->\n\n')

            # write the topheadline
            f.write(f'# {self.name}\n\n')

            if self.summary is not None:
                # write the summary
                f.write(f'## Summary\n\n')
                f.write(f'{self.summary}\n')
                f.write(f'\n')

            if self.description is not None:
                # write the description
                f.write(f'## Description\n\n')
                f.write(f'{self.description}\n')
                f.write(f'\n')

            # write the metadata
            f.write(f'## Metadata\n\n')
            for name, val in self.metadata.items():
                f.write(f'- {name}: {" ".join(val)}\n')
            f.write('\n')

            # write the entries
            f.write(f'## Entries\n\n')
            for name, val in self.entries.items():
                f.write(f'- {name}: {val}\n')
# loaders of the various file types of the model

# SPDX-License-Identifier: Apache-2.0

import logging

from .mdparsing import ContentSection, NestedListSection, SingleListSection, SpecFile

logger = logging.getLogger(__name__)


class NamespaceLoader:
    def __init__(self, fname):
        sf = SpecFile(fname)
        self.license = sf.license
        self.name = sf.name

        s = ContentSection(sf.sections["Summary"])
        self.summary = s.content

        s = ContentSection(sf.sections["Description"])
        self.description = s.content

        s = SingleListSection(sf.sections["Metadata"])
        self.metadata = s.kv


class ClassLoader:
    def __init__(self, fname):
        sf = SpecFile(fname)
        self.license = sf.license
        self.name = sf.name

        s = ContentSection(sf.sections["Summary"])
        self.summary = s.content

        s = ContentSection(sf.sections["Description"])
        self.description = s.content

        s = SingleListSection(sf.sections["Metadata"])
        self.metadata = s.kv

        s = NestedListSection(sf.sections["Properties"])
        self.properties = s.ikv


class PropertyLoader:
    def __init__(self, fname):
        sf = SpecFile(fname)
        self.license = sf.license
        self.name = sf.name

        s = ContentSection(sf.sections["Summary"])
        self.summary = s.content

        s = ContentSection(sf.sections["Description"])
        self.description = s.content

        s = SingleListSection(sf.sections["Metadata"])
        self.metadata = s.kv


class VocabularyLoader:
    def __init__(self, fname):
        sf = SpecFile(fname)
        self.license = sf.license
        self.name = sf.name

        s = ContentSection(sf.sections["Summary"])
        self.summary = s.content

        s = ContentSection(sf.sections["Description"])
        self.description = s.content

        s = SingleListSection(sf.sections["Metadata"])
        self.metadata = s.kv

        s = SingleListSection(sf.sections["Entries"])
        self.entries = s.kv


class IndividualLoader:
    def __init__(self, fname):
        sf = SpecFile(fname)
        self.license = sf.license
        self.name = sf.name

        s = ContentSection(sf.sections["Summary"])
        self.summary = s.content

        s = ContentSection(sf.sections["Description"])
        self.description = s.content

        s = SingleListSection(sf.sections["Metadata"])
        self.metadata = s.kv

        s = SingleListSection(sf.sections["Property Values"])
        self.values = s.kv


class DatatypeLoader:
    def __init__(self, fname):
        sf = SpecFile(fname)
        self.license = sf.license
        self.name = sf.name

        s = ContentSection(sf.sections["Summary"])
        self.summary = s.content

        s = ContentSection(sf.sections["Description"])
        self.description = s.content

        s = SingleListSection(sf.sections["Metadata"])
        self.metadata = s.kv

        s = SingleListSection(sf.sections["Format"])
        self.format = s.kv

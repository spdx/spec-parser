# in-memory representation of the model

# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path


from .mdparsing import (
    SpecFile,
    ContentSection,
    SingleListSection,
    NestedListSection,
)

class Model:

    def __init__ (self, dir = None):
        self.name = None
        self.namespaces = []
        self.classes = dict()
        self.properties = dict()
        self.vocabularies = dict()
        self.individuals = dict()
        self.datatypes = dict()

        if dir is not None:
            self.load(dir)

    def load(self, dir):
        self.toplevel = p = Path(dir)
        if not p.is_dir():
            logging.error(f"{dir}: not a directory")
            return
        if p.name != "model":
            logging.warning(f'{dir}: input not named "model"')

        for d in [d for d in p.iterdir() if d.is_dir() and d.name[0].isupper()]:
            nsp = p / d.name / f"{d.name}.md"
            if not nsp.is_file():
                logging.error(f"Missing top-level namespace file {nsp.name}")
                continue
            
            ns = Namespace(nsp)
            self.namespaces.append(ns)

            dp = p / d.name / "Classes"
            if dp.is_dir():
                for f in [f for f in dp.iterdir() if f.is_file() and f.name[0].isupper() and f.name.endswith(".md")]:
                    n = Class(f, ns)
                    k = n.fqname
                    self.classes[k] = n
                    ns.classes[k] = n

            dp = p / d.name / "Properties"
            if dp.is_dir():
                for f in [f for f in dp.iterdir() if f.is_file() and f.name[0].islower() and f.name.endswith(".md")]:
                    n = Property(f, ns)
                    k = n.fqname
                    self.properties[k] = n
                    ns.properties[k] = n

            dp = p / d.name / "Vocabularies"
            if dp.is_dir():
                for f in [f for f in dp.iterdir() if f.is_file() and f.name[0].isupper() and f.name.endswith(".md")]:
                    n = Vocabulary(f, ns)
                    k = n.fqname
                    self.vocabularies[k] = n
                    ns.vocabularies[k] = n

            dp = p / d.name / "Individuals"
            if dp.is_dir():
                for f in [f for f in dp.iterdir() if f.is_file() and f.name[0].isupper() and f.name.endswith(".md")]:
                    n = Individual(f, ns)
                    k = n.fqname
                    self.individuals[k] = n
                    ns.individuals[k] = n

            dp = p / d.name / "Datatypes"
            if dp.is_dir():
                for f in [f for f in dp.iterdir() if f.is_file() and f.name[0].isupper() and f.name.endswith(".md")]:
                    n = Datatype(f, ns)
                    k = n.fqname
                    self.datatypes[k] = n
                    ns.datatypes[k] = n

        # processing
        # TODO
        # add links from properties to classes using them
        # add inherited properties to classes
        self.types = self.classes | self.vocabularies | self.datatypes

        logging.info(f"Loaded {len(self.namespaces)} namespaces, {len(self.classes)} classes, {len(self.properties)} properties, {len(self.vocabularies)} vocabularies, {len(self.individuals)} individuals, {len(self.datatypes)} datatypes")
        logging.info(f"Total {len(self.types)} types")

        for c in self.classes.values():
            for p, pkv in c.properties.items():
                pname = "" if p.startswith("/") else f"/{c.ns.name}/"
                pname += p
                proptype = self.properties[pname].metadata["Range"]
                ptype = pkv["type"]
                if proptype != ptype:
                    if not p.startswith("/"):
                        logging.error(f"In class {c.fqname}, property {p} has type {ptype} but the range of {pname} is {proptype}")
                    else:
                        if proptype.rpartition('/')[-1] != ptype.rpartition('/')[-1]:
                            logging.error(f"In class {c.fqname}, property {p} has type {ptype} but the range of {pname} is {proptype}")
                # del pkv["type"] # not needed any more, info is on property
                self.properties[pname].used_in.append(c.fqname)

        # TODO
        # add inherited properties to classes


    def gen_all(self, dir, cfg):
        from .jsondump import gen_jsondump
        from .mkdocs import gen_mkdocs
        from .plantuml import gen_plantuml
        from .rdf import gen_rdf

        gen_mkdocs(self, dir, cfg)
        gen_rdf(self, dir, cfg)
        gen_plantuml(self, dir, cfg)
        gen_jsondump(self, dir, cfg)



class Namespace:
    def __init__(self, fname):
        self.classes = dict()
        self.properties = dict()
        self.vocabularies = dict()
        self.individuals = dict()
        self.datatypes = dict()

        sf = SpecFile(fname)
        self.license = sf.license
        self.name = sf.name

        s = ContentSection(sf.sections["Summary"])
        self.summary = s.content

        s = ContentSection(sf.sections["Description"])
        self.description = s.content

        s = SingleListSection(sf.sections["Metadata"])
        self.metadata = s.kv

        # checks
        assert self.name == self.metadata["name"], f"Namespace name {self.name} does not match metadata {self.metadata['name']}"

        # processing
        self.iri = self.metadata["id"]


class Class:
    VALID_METADATA = (
        "Instantiability",
        "name",
        "SubclassOf",
    )
    VALID_PROP_METADATA = (
        "maxCount",
        "minCount",
        "type",
    )
    def __init__(self, fname, ns):
        self.ns = ns

        # parsing
        sf = SpecFile(fname)
        self.license = sf.license
        self.name = sf.name
        self.fqname = f"/{ns.name}/{sf.name}"

        s = ContentSection(sf.sections["Summary"])
        self.summary = s.content

        s = ContentSection(sf.sections["Description"])
        self.description = s.content

        s = SingleListSection(sf.sections["Metadata"])
        self.metadata = s.kv

        if "Properties" in sf.sections:
            s = NestedListSection(sf.sections["Properties"])
            self.properties = s.ikv
        else:
            self.properties = dict()

        # checks
        assert self.name == self.metadata["name"], f"Class name {self.name} does not match metadata {self.metadata['name']}"
        for p in self.metadata:
            assert p in self.VALID_METADATA, f"Unknown toplevel key '{p}'"
        for prop in self.properties:
            for p in self.properties[prop]:
                assert p in self.VALID_PROP_METADATA, f"Unknown nested key '{p}'"

        # processing
        self.iri = f"{self.ns.iri}/{self.name}"
        if "Instantiability" not in self.metadata:
            self.metadata["Instantiability"] = "Concrete"
        if self.metadata.get("SubclassOf") == "none":
            del self.metadata["SubclassOf"]
        for prop in self.properties:
            self.properties[prop]["fqname"] = prop if prop.startswith('/') else f"/{ns.name}/{prop}"
            if "minCount" not in self.properties[prop]:
                self.properties[prop]["minCount"] = 0
            if "maxCount" not in self.properties[prop]:
                self.properties[prop]["maxCount"] = '*'


       
class Property:
    VALID_METADATA = (
        "name",
        "Nature",
        "Range",
    )
    def __init__(self, fname, ns):
        self.ns = ns

        sf = SpecFile(fname)
        self.license = sf.license
        self.name = sf.name
        self.fqname = f"/{ns.name}/{sf.name}"

        s = ContentSection(sf.sections["Summary"])
        self.summary = s.content

        s = ContentSection(sf.sections["Description"])
        self.description = s.content

        s = SingleListSection(sf.sections["Metadata"])
        self.metadata = s.kv

        # checks
        assert self.name == self.metadata["name"], f"Property name {self.name} does not match metadata {self.metadata['name']}"
        for p in self.metadata:
            assert p in self.VALID_METADATA, f"Unknown toplevel key '{p}'"
        for p in self.VALID_METADATA:
            assert p in self.metadata, f"Missing {p} in property {self.fqname}"

        # processing
        self.iri = f"{self.ns.iri}/{self.name}"
        self.used_in = []


class Vocabulary:
    VALID_METADATA = (
        "name",
    )
    def __init__(self, fname, ns):
        self.ns = ns

        sf = SpecFile(fname)
        self.license = sf.license
        self.name = sf.name
        self.fqname = f"/{ns.name}/{sf.name}"

        s = ContentSection(sf.sections["Summary"])
        self.summary = s.content

        s = ContentSection(sf.sections["Description"])
        self.description = s.content

        s = SingleListSection(sf.sections["Metadata"])
        self.metadata = s.kv

        s = SingleListSection(sf.sections["Entries"])
        self.entries = s.kv

        # checks
        assert self.name == self.metadata["name"], f"Vocabulary name {self.name} does not match metadata {self.metadata['name']}"
        for p in self.metadata:
            assert p in self.VALID_METADATA, f"Unknown toplevel key '{p}'"

        # processing
        self.iri = f"{self.ns.iri}/{self.name}"



class Individual:
    VALID_METADATA = (
        "name",
        "type",
        "IRI",
    )
    def __init__(self, fname, ns):
        self.ns = ns

        sf = SpecFile(fname)
        self.license = sf.license
        self.name = sf.name
        self.fqname = f"/{ns.name}/{sf.name}"

        s = ContentSection(sf.sections["Summary"])
        self.summary = s.content

        s = ContentSection(sf.sections["Description"])
        self.description = s.content

        s = SingleListSection(sf.sections["Metadata"])
        self.metadata = s.kv

        s = SingleListSection(sf.sections["Property Values"])
        self.values = s.kv

        # checks
        assert self.name == self.metadata["name"], f"Individual name {self.name} does not match metadata {self.metadata['name']}"
        for p in self.metadata:
            assert p in self.VALID_METADATA, f"Unknown toplevel key '{p}'"

        # processing
        self.iri = f"{self.ns.iri}/{self.name}"



class Datatype:
    VALID_METADATA = (
        "name",
        "SubclassOf",
    )
    def __init__(self, fname, ns):
        self.ns = ns

        sf = SpecFile(fname)
        self.license = sf.license
        self.name = sf.name
        self.fqname = f"/{ns.name}/{sf.name}"

        s = ContentSection(sf.sections["Summary"])
        self.summary = s.content

        s = ContentSection(sf.sections["Description"])
        self.description = s.content

        s = SingleListSection(sf.sections["Metadata"])
        self.metadata = s.kv

        s = SingleListSection(sf.sections["Format"])
        self.format = s.kv

        # checks
        assert self.name == self.metadata["name"], f"Datatype name {self.name} does not match metadata {self.metadata['name']}"
        for p in self.metadata:
            assert p in self.VALID_METADATA, f"Unknown toplevel key '{p}'"

        # processing
        self.iri = f"{self.ns.iri}/{self.name}"


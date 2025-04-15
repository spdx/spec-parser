# in-memory representation of the model

# SPDX-License-Identifier: Apache-2.0

import logging
from copy import deepcopy

from .mdparsing import (
    ContentSection,
    NestedListSection,
    SingleListSection,
    SpecFile,
)

logger = logging.getLogger(__name__)

class Model:
    def __init__(self, inpath=None):
        self.name = None
        self.namespaces = []
        self.classes = dict()
        self.properties = dict()
        self.vocabularies = dict()
        self.individuals = dict()
        self.datatypes = dict()

        if inpath is not None:
            self.load(inpath)

    def load(self, inpath):
        p = inpath

        for d in [d for d in p.iterdir() if d.is_dir() and d.name[0].isupper()]:
            nsp = p / d.name / f"{d.name}.md"
            if not nsp.is_file():
                logger.error(f"Missing top-level namespace file {nsp.name}")
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

        logger.info(
            f"Loaded {len(self.namespaces)} namespaces, {len(self.classes)} classes, "
            f"{len(self.properties)} properties, {len(self.vocabularies)} vocabularies, "
            f"{len(self.individuals)} individuals, {len(self.datatypes)} datatypes",
        )
        self.process_after_load()

    def process_after_load(self):
        self.types = self.classes | self.vocabularies | self.datatypes
        logger.info(f"Total {len(self.types)} types")

        # add used_in information to properties
        for c in self.classes.values():
            for p, pkv in c.properties.items():
                pname = "" if p.startswith("/") else f"/{c.ns.name}/"
                pname += p
                proptype = self.properties[pname].metadata["Range"]
                ptype = pkv["type"]
                if proptype != ptype and (not p.startswith("/") or proptype.rpartition("/")[-1] != ptype.rpartition("/")[-1]):
                    logger.error(f"In class {c.fqname}, property {p} has type {ptype} but the range of {pname} is {proptype}")
                self.properties[pname].used_in.append(c.fqname)

        # add class inheritance stack
        inheritances = []
        for c in self.classes.values():
            parent = c.fqsupercname
            if parent:
                inheritances.append((c.fqname, parent))

        def _tsort_recursive(inh, cn, visited, stack):
            visited[cn] = True
            for ipair in inh:
                (chd, par) = ipair
                if chd == cn:
                    if not visited[par]:
                        _tsort_recursive(inh, par, visited, stack)
            stack.append(cn)

        visited = {c.fqname: False for c in self.classes.values()}
        stack = []
        for c in self.classes.values():
            if not visited[c.fqname]:
                _tsort_recursive(inheritances, c.fqname, visited, stack)
        for cn in stack:
            c = self.classes[cn]
            c.inheritance_stack = []
            pcn = c.fqsupercname
            while pcn:
                c.inheritance_stack.append(pcn)
                pcn = self.classes[pcn].fqsupercname

        # build subclass trees
        # Initialize subclasses dict for each class
        for c in self.classes.values():
            c.subclasses = []

        # Populate subclasses
        for c in self.classes.values():
            if c.fqsupercname:
                self.classes[c.fqsupercname].subclasses.append(c.fqname)

        # Sort subclasses by name for consistent display
        for c in self.classes.values():
            c.subclasses.sort()

        # add inherited properties to classes
        for cn in stack:
            c = self.classes[cn]
            c.all_properties = dict()
            for p, pkv in c.properties.items():
                shortname = p.rpartition("/")[-1]
                fullname = "" if p.startswith("/") else f"/{c.ns.name}/"
                fullname += p
                fulltype = "" if pkv["type"].startswith("/") or pkv["type"].startswith("xsd:") else f"/{c.ns.name}/"
                fulltype += pkv["type"]
                c.all_properties[shortname] = deepcopy(pkv)
                c.all_properties[shortname]["fullname"] = fullname
                c.all_properties[shortname]["fulltype"] = fulltype

            if c.inheritance_stack:
                p = c.inheritance_stack[0]
                c.all_properties.update(deepcopy(self.classes[p].all_properties))

            if c.ext_prop_restrs:
                for p, pkv in c.ext_prop_restrs.items():
                    (_, pns, _, shortname) = p.split("/")
                    assert c.all_properties[shortname]["fullname"] == f"/{pns}/{shortname}"
                    for k, v in pkv.items():
                        if c.all_properties[shortname][k] == v:
                            logger.warning(f"In class {c.fqname} property {p} has same {k} as the parent class")
                        c.all_properties[shortname][k] = v

    def generate(self, cfg):
        if cfg.generate_jsondump:
            from .jsondump import gen_jsondump
            gen_jsondump(self, cfg.output_jsondump_path, cfg)
        if cfg.generate_mkdocs:
            from .mkdocs import gen_mkdocs
            gen_mkdocs(self, cfg.output_mkdocs_path, cfg)
        if cfg.generate_plantuml:
            from .plantuml import gen_plantuml
            gen_plantuml(self, cfg.output_plantuml_path, cfg)
        if cfg.generate_rdf:
            from .rdf import gen_rdf
            gen_rdf(self, cfg.output_rdf_path, cfg)
        if cfg.generate_tex:
            from .tex import gen_tex
            gen_tex(self, cfg.output_tex_path, cfg)
        if cfg.generate_webpages:
            from .webpages import gen_webpages
            gen_webpages(self, cfg.output_webpages_path, cfg)


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

        if "Profile conformance" in sf.sections:
            s = ContentSection(sf.sections["Profile conformance"])
            self.conformance = s.content
        else:
            self.conformance = None

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

        if "External properties restrictions" in sf.sections:
            s = NestedListSection(sf.sections["External properties restrictions"])
            self.ext_prop_restrs = s.ikv
        else:
            self.ext_prop_restrs = dict()

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
            self.properties[prop]["fqname"] = prop if prop.startswith("/") else f"/{ns.name}/{prop}"
            if "minCount" not in self.properties[prop]:
                self.properties[prop]["minCount"] = 0
            if "maxCount" not in self.properties[prop]:
                self.properties[prop]["maxCount"] = "*"

        parent = self.metadata.get("SubclassOf")
        if parent:
            if not parent.startswith("/"):
                parent = f"/{ns.name}/{parent}"
        self.fqsupercname = parent


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
    VALID_METADATA = ("name",)

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
        if "IRI" not in self.metadata:
            self.metadata["IRI"] = self.iri


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

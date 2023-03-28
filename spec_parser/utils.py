import logging
import re
from os import path
from typing import List

import rdflib
from rdflib import URIRef, Literal, SH, BNode
from rdflib.namespace import RDF, OWL, RDFS, XSD

NS0 = rdflib.Namespace("http://www.w3.org/2003/06/sw-vocab-status/ns#")

from .helper import (
    isError,
    safe_open,
    union_dict,
)
from .config import id_metadata_prefix, metadata_defaults, property_defaults
from .__version__ import __version__

__all__ = ["Spec", "SpecClass", "SpecProperty", "SpecVocab"]


class Spec:
    """Class for storing Specification.

    .. warning:: This is not meant for direct usage.

    This class is used to store all the namespaces
    (including all entities inside it). This class also maintain
    Spec level information like references and name of all entities
    and namespaces.

    Args:
        spec_dir (str): path to specs directory
        args (dict): output specific arguments
    """

    def __init__(self, spec_dir: str, args: dict):

        self.spec_dir = spec_dir
        self.namespaces = dict()
        self.logger = logging.getLogger(self.__class__.__name__)

        # will store all classes that references certain data property
        self.dataprop_refs = dict()

        # output specific arguments
        self.args = args
        self.args.setdefault("gen_refs", False)
        self.args.setdefault("use_table", False)
        self.args.setdefault("out_dir", "md_generated")

    def add_namespace(
        self, name: str, classes: List, properties: List, vocabs: List
    ) -> None:
        """Add namespace information into Specfication.

        Args:
            name (str): name of the namepaces
            classes (List): All `Class` entities inside namespace
            properties (List): All `Porperty` entities inside namespace
            vocabs (List): All `Vocab` entities inside namespace
        """

        class_dict = dict()
        props_dict = dict()
        vocabs_dict = dict()

        for _class in classes:
            if _class.name in class_dict:
                # report error
                self.logger.error(
                    "Duplicate `Class` object found: '{name}:{_class.name}'"
                )

            class_dict[_class.name] = _class

        for _prop in properties:
            if _prop.name in props_dict:
                # report error
                self.logger.error(
                    "Duplicate `Property` object found: '{name}:{_prop.name}'"
                )

            props_dict[_prop.name] = _prop

        for _vocab in vocabs:
            if _vocab.name in vocabs_dict:
                # report error
                self.logger.error(
                    "Duplicate `Vocab` object found: '{name}:{_vocab.name}'"
                )

            vocabs_dict[_vocab.name] = _vocab

        namespace_el = {
            "name": name,
            "classes": class_dict,
            "properties": props_dict,
            "vocabs": vocabs_dict,
        }

        if name in self.namespaces:
            self.logger.error(f"Namespace with name: {name} already exists")

        self.namespaces[name] = namespace_el

    def gen_md(self) -> None:
        """Generate pretty markdowns."""
        # if we have encounter error then terminate
        if isError():
            self.logger.warning(f"Specs not parsed succesfully, aborting the gen_md...")
            return

        if path.isdir(self.args["out_dir"]):
            self.logger.warning(f"Overwriting out_dir `{self.args['out_dir']}`")

        for namespace in self.namespaces.values():

            classes = namespace["classes"]
            properties = namespace["properties"]
            vocabs = namespace["vocabs"]

            for class_obj in classes.values():
                class_obj._gen_md(self.args)

            for prop_obj in properties.values():
                prop_obj._gen_md(self.args)

            for vocab_obj in vocabs.values():
                vocab_obj._gen_md(self.args)

    def gen_rdf(self) -> None:
        """Generate RDF in turtle format."""

        g = rdflib.Graph()

        g.bind("owl", OWL)
        g.bind("ns0", NS0)

        self.rdf_dict = {"ns0": NS0, "rdf": RDF, "owl": OWL, "rdfs": RDFS, "xsd": XSD}

        # add all namespaces
        for _name in self.namespaces.keys():
            self.rdf_dict[_name] = rdflib.Namespace(f"{id_metadata_prefix}{_name}#")
            g.bind(_name.lower(), self.rdf_dict[_name])

        # add triples starting from each namespaces
        for _namespace in self.namespaces.values():

            classes = _namespace["classes"]
            properties = _namespace["properties"]
            vocabs = _namespace["vocabs"]

            for class_obj in classes.values():
                class_obj._gen_rdf(g)

            for prop_obj in properties.values():
                prop_obj._gen_rdf(g)

            for vocab_obj in vocabs.values():
                vocab_obj._gen_rdf(g)

        # if we have encounter error then terminate
        if isError():
            self.logger.warning(f"Error parsing the spec. Aborting the gen_rdf...")
            return

        fname = path.join(self.args["out_dir"], f"tst.ttl")
        with safe_open(fname, "w") as f:
            f.write(g.serialize(format="turtle"))

    def gen_shacl(self) -> None:
        """Generate SHACL in turtle format."""

        g = rdflib.Graph()

        g.bind("owl", OWL)
        g.bind("ns0", NS0)
        g.bind("sh", SH)

        self.rdf_dict = {"ns0": NS0, "rdf": RDF, "owl": OWL, "rdfs": RDFS, "xsd": XSD, "sh": SH}

        # add all namespaces
        for _name in self.namespaces.keys():
            self.rdf_dict[_name] = rdflib.Namespace(f"{id_metadata_prefix}{_name}#")
            g.bind(_name.lower(), self.rdf_dict[_name])

        # add triples starting from each namespaces
        for _namespace in self.namespaces.values():

            classes = _namespace["classes"]

            for class_obj in classes.values():
                class_obj._gen_shacl(g)

        # if we have encounter error then terminate
        if isError():
            self.logger.warning(f"Error parsing the spec. Aborting the gen_shacl...")
            return

        fname = path.join(self.args["out_dir"], f"model_shacl.ttl")
        with safe_open(fname, "w") as f:
            f.write(g.serialize(format="turtle"))


class SpecBase:
    def __init__(
        self,
        spec: Spec,
        namespace_name: str,
        name: str,
        summary: str,
        description: str,
        license_name: str
    ):

        self.logger: logging.Logger = None
        self.spec: Spec = spec
        self.namespace_name: str = namespace_name
        self.name: str = name
        self.summary: str = summary
        self.description: str = description
        self.license_name: str = license_name
        self.metadata: dict = dict()
        self.properties: dict = dict()
        self.entries: dict = dict()

    def _extract_metadata(self, mdata_list):

        for _dict in mdata_list:

            _key = _dict["name"]
            _values = _dict["values"]

            if _key in self.metadata:
                # report the error
                self.logger.error(f"{self.name}: Metadata key '{_key}' already exists")

            self.metadata[_key] = _values

        # add all default metadata fields
        union_dict(self.metadata, metadata_defaults)

        # add id metadata
        self.metadata["id"] = [f"{id_metadata_prefix}{self.namespace_name}#{self.name}"]

    def _extract_properties(self, props_list):

        for prop in props_list:

            name = prop["name"]
            avline_list = prop["values"]

            subprops_dict = dict()

            for avline in avline_list:

                _key = avline["name"]
                _values = avline["values"]

                if _key in subprops_dict:
                    # report the error
                    self.logger.error(
                        f"{self.name}: Attribute key '{_key}' already exists in data property '{name}'"
                    )

                subprops_dict[_key] = _values

            if name in self.properties:
                # report the error
                self.logger.error(f"{self.name}: Data property `{_key}` already exists")

            # add all default property fields
            union_dict(subprops_dict, property_defaults)

            self.properties[name] = subprops_dict

        # populate all refs to data property
        for dataprop in self.properties.keys():

            if dataprop not in self.spec.dataprop_refs:
                self.spec.dataprop_refs[dataprop] = []

            self.spec.dataprop_refs[dataprop].append(
                f"{self.namespace_name}:{self.name}"
            )

    def _extract_entries(self, entry_list):

        for entry in entry_list:

            _key = entry["name"]
            _value = entry["value"]

            if _key in self.entries:
                # report the error
                self.logger.error(f"{self.name}: Entry '{_key}' already exists")

            self.entries[_key] = _value

    def _gen_uri(self, entity):

        splitted = re.split(r":", entity)

        if len(splitted) > 2:
            return Literal(entity)

        if getattr(self, "spec", None) is None:
            return Literal(entity)

        rdf_dict = self.spec.rdf_dict

        if len(splitted) == 1:
            _namespace = self.namespace_name
        else:
            _namespace = splitted[0]

        if _namespace not in rdf_dict:
            return Literal(entity)

        return rdf_dict[_namespace][splitted[-1]]


class SpecClass(SpecBase):
    """This class store the parsed information of `Class` entity.

    .. warning:: This is not meant for direct usage.

    Args:
        spec (Spec): Parent Spec object
        namespace_name (str): name of namespace
        name (str): name of `Class` entity
        summary (str): summary of this entity
        description (str): description of this entity
        metadata (dict): metadata of this entity
        props (dict): properties of this entity
    """

    def __init__(
        self,
        spec: Spec,
        namespace_name: str,
        name: str,
        summary: str,
        description: str,
        metadata: dict,
        props: dict,
        license_name: str
    ):

        super().__init__(
            spec,
            namespace_name,
            name,
            summary,
            description,
            license_name
        )

        self.logger = logging.getLogger(self.__class__.__name__)
        self._extract_metadata(metadata)
        self._extract_properties(props)

    def _gen_md(self, args: dict) -> None:

        fname = path.join(
            args["out_dir"], self.namespace_name, "Classes", f"{self.name}.md"
        )

        with safe_open(fname, "w") as f:

            # write the header
            f.write(
                f"<!-- Auto generated markdown by Spec-parser v{__version__} -->\n\n"
            )

            # write the license name
            f.write(
                f"<!-- SPDX-License-Identifier: {self.license_name} -->\n\n"
            )

            # write the topheadline
            f.write(f"# {self.name}\n\n")

            # write the summary
            f.write(f"## Summary\n\n")
            f.write(f"{self.summary}\n")
            f.write(f"\n")

            # write the description
            f.write(f"## Description\n\n")
            f.write(f"{self.description}\n")
            f.write(f"\n")

            # write the metadata
            f.write(f"## Metadata\n\n")
            for name, vals in self.metadata.items():
                f.write(f'- {name}: {" ".join(vals)}\n')
            f.write("\n")

            # write the data_props
            f.write(f"## Properties\n\n")
            if args.get("use_table", False):
                # generate markdown-table from properties
                header_list = ["type", "minCount", "maxCount"]

                # print the header
                f.write("|" + "|".join(["property"] + header_list) + "|\n")
                f.write("|" + "---|" * (len(header_list) + 1) + "\n")

                for name, subprops in self.properties.items():
                    f.write(f"|{name}")
                    for subprop in header_list:
                        f.write(f'|{" ".join(subprops.get(subprop, ["NA"]))}')
                    f.write("|\n")
            else:
                # generate markdown-list from properties
                for name, subprops in self.properties.items():
                    f.write(f"- {name}\n")
                    for _key, subprop in subprops.items():
                        f.write(f'  - {_key}: {" ".join(subprop)}\n')
                    f.write("\n")
            
            # license declaration
            f.write(f"\nSPDX-License-Identifier: {self.license_name}")

    def _gen_rdf(self, g: rdflib.Graph) -> None:

        # self.spec.rdf_dict
        cur = URIRef(self.metadata["id"][0])

        g.add((cur, RDF.type, OWL["Class"]))

        for subclass in self.metadata.get("SubclassOf", []):
            g.add((cur, RDFS.subClassOf, self._gen_uri(subclass)))

        g.add((cur, RDFS.comment, Literal(self.description)))
        g.add((cur, NS0.term_status, Literal(self.metadata.get("Status")[0])))

    def _gen_shacl(self, g: rdflib.Graph) -> None:

        class_uri = URIRef(self.metadata["id"][0])
        shape_uri = URIRef(self.metadata["id"][0] + "Shape")

        g.add((shape_uri, RDF.type, SH.NodeShape))
        g.add((shape_uri, SH.targetClass, class_uri))

        for prop_name, prop_value in self.properties.items():
            property_uri = self._gen_uri(prop_name)
            property_type_uri = self._gen_uri(prop_value["type"][0])
            min_count: str = prop_value["minCount"][0]
            max_count: str = prop_value["maxCount"][0]

            restriction_node = BNode()
            g.add((restriction_node, SH.path, property_uri))
            g.add((restriction_node, SH.datatype, property_type_uri))
            g.add((restriction_node, SH.name, Literal(prop_name)))
            if min_count != "0":
                g.add((restriction_node, SH.minCount, Literal(int(min_count))))
            if max_count != "*":
                g.add((restriction_node, SH.maxCount, Literal(int(max_count))))

            g.add((shape_uri, SH.property, restriction_node))


class SpecProperty(SpecBase):
    """This class store the parsed information of `Property` entity.

    .. warning:: This is not meant for direct usage.

    Args:
        spec (Spec): Parent Spec object
        namespace_name (str): name of namespace
        name (str): name of `Class` entity
        summary (str): summary of this entity
        description (str): description of this entity
        metadata (dict): metadata of this entity
    """

    def __init__(
        self,
        spec: Spec,
        namespace_name: str,
        name: str,
        summary: str,
        description: str,
        metadata: dict,
        license_name: str
    ):

        super().__init__(
            spec,
            namespace_name,
            name,
            summary,
            description,
            license_name
        )

        self.logger = logging.getLogger(self.__class__.__name__)
        self._extract_metadata(metadata)

    def _gen_md(self, args: dict) -> None:

        fname = path.join(
            args["out_dir"], self.namespace_name, "Properties", f"{self.name}.md"
        )

        with safe_open(fname, "w") as f:

            # write the header
            f.write(
                f"<!-- Auto generated markdown by Spec-parser v{__version__} -->\n\n"
            )

            # write the license name
            f.write(
                f"<!-- SPDX-License-Identifier: {self.license_name} -->\n\n"
            )

            # write the topheadline
            f.write(f"# {self.name}\n\n")

            # write the summary
            f.write(f"## Summary\n\n")
            f.write(f"{self.summary}\n")
            f.write(f"\n")

            # write the description
            f.write(f"## Description\n\n")
            f.write(f"{self.description}\n")
            f.write(f"\n")

            # write the metadata
            f.write(f"## Metadata\n\n")
            for name, val in self.metadata.items():
                f.write(f'- {name}: {" ".join(val)}\n')
            f.write(f"\n")

            if args.get("gen_refs", False):
                # Class references
                f.write(f"## References\n\n")
                for name in self.spec.dataprop_refs.get(self.name, []):
                    f.write(f"- {name}\n")

            # license declaration
            f.write(f"\nSPDX-License-Identifier: {self.license_name}")

    def _gen_rdf(self, g: rdflib.Graph) -> None:

        # self.spec.rdf_dict
        cur = URIRef(self.metadata["id"][0])

        # nature of property
        for _nature in self.metadata.get("Nature", []):
            if _nature == "ObjectProperty":
                _mask = OWL["ObjectProperty"]
            elif _nature == "DataProperty":
                _mask = OWL["DatatypeProperty"]
            else:
                self.logger.error(f"Invalid Nature attribute in metadata `{_nature}`")
                continue

            g.add((cur, RDF.type, _mask))

        for _val in self.metadata.get("Range", []):
            g.add((cur, RDFS.range, self._gen_uri(_val)))

        for _val in self.metadata.get("Domain", []):
            g.add((cur, RDFS.domain, self._gen_uri(_val)))

        g.add((cur, RDFS.comment, Literal(self.description)))
        g.add((cur, NS0.term_status, Literal(self.metadata.get("Status")[0])))


class SpecVocab(SpecBase):
    """This class store the parsed information of `Vocab` entity.

    .. warning:: This is not meant for direct usage.

    Args:
        spec (Spec): Parent Spec object
        namespace_name (str): name of namespace
        name (str): name of `Class` entity
        summary (str): summary of this entity
        description (str): description of this entity
        metadata (dict): metadata of this entity
        entries (dict): entries of this entity
    """

    def __init__(
        self,
        spec: Spec,
        namespace_name: str,
        name: str,
        summary: str,
        description: str,
        metadata: dict,
        entries: dict,
        license_name: str,
    ):

        super().__init__(
            spec,
            namespace_name,
            name,
            summary,
            description,
            license_name,
        )

        self.logger = logging.getLogger(self.__class__.__name__)
        self._extract_metadata(metadata)
        self._extract_entries(entries)

    def _gen_md(self, args: dict) -> None:

        fname = path.join(
            args["out_dir"], self.namespace_name, "Vocabularies", f"{self.name}.md"
        )

        with safe_open(fname, "w") as f:

            # write the header
            f.write(
                f"<!-- Auto generated markdown by Spec-parser v{__version__} -->\n\n"
            )

            # write the license name
            f.write(
                f"<!-- SPDX-License-Identifier: {self.license_name} -->\n\n"
            )

            # write the topheadline
            f.write(f"# {self.name}\n\n")

            # write the summary
            f.write(f"## Summary\n\n")
            f.write(f"{self.summary}\n")
            f.write(f"\n")

            # write the description
            f.write(f"## Description\n\n")
            f.write(f"{self.description}\n")
            f.write(f"\n")

            # write the metadata
            f.write(f"## Metadata\n\n")
            for name, val in self.metadata.items():
                f.write(f'- {name}: {" ".join(val)}\n')
            f.write("\n")

            # write the entries
            f.write(f"## Entries\n\n")
            for name, val in self.entries.items():
                f.write(f"- {name}: {val}\n")

            # license declaration
            f.write(f"\nSPDX-License-Identifier: {self.license_name}")

    def _gen_rdf(self, g: rdflib.Graph):

        cur = URIRef(self.metadata["id"][0])
        g.add((cur, RDF.type, OWL["Class"]))

        g.add((cur, RDFS.comment, Literal(self.description)))
        g.add((cur, NS0.term_status, Literal(self.metadata.get("Status")[0])))

        # add entries
        for _entry, _desc in self.entries.items():
            g.add((self._gen_uri(_entry), RDF.type, OWL.NamedIndividual))
            g.add((self._gen_uri(_entry), RDF.type, cur))

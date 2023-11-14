import json
import logging
import re
from os import path
from typing import List

from jinja2 import Environment, PackageLoader

import rdflib
from rdflib import URIRef, Literal, BNode, SH
from rdflib.extras.infixowl import EnumeratedClass
from rdflib.namespace import RDF, OWL, RDFS, XSD

from .owl_to_context import convert_spdx_owl_to_jsonld_context

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

        if path.isdir(self.args["out_dir"]):
            self.logger.warning(f"Overwriting out_dir `{self.args['out_dir']}`")

        env = Environment(
            loader=PackageLoader("spec_parser", package_path="templates/default"),
            autoescape=False
        )

        for namespace in self.namespaces.values():

            classes = namespace["classes"]
            properties = namespace["properties"]
            vocabs = namespace["vocabs"]

            for class_obj in classes.values():
                class_obj._gen_md(env, self.args)

            for prop_obj in properties.values():
                prop_obj._gen_md(env, self.args)

            for vocab_obj in vocabs.values():
                vocab_obj._gen_md(env, self.args)

    def _get_defined_class_types(self) -> List[URIRef]:
        class_types = []
        for _namespace in self.namespaces.values():
            classes = _namespace["classes"]
            vocabs = _namespace["vocabs"]
            class_types += [URIRef(c.metadata["id"]) for c in classes.values() if not c.is_literal()]
            class_types += [URIRef(v.metadata["id"]) for v in vocabs.values()]

        return class_types

    def gen_rdf(self) -> None:
        """Generate RDF in turtle format."""

        g = rdflib.Graph()

        g.bind("owl", OWL)
        g.bind("ns0", NS0)
        g.bind("sh", SH)

        self.rdf_dict = {"ns0": NS0, "rdf": RDF, "owl": OWL, "rdfs": RDFS, "xsd": XSD, "sh": SH}

        # add all namespaces
        for _name in self.namespaces.keys():
            self.rdf_dict[_name] = rdflib.Namespace(f"{id_metadata_prefix}{_name}/")
            g.bind(_name.lower(), self.rdf_dict[_name])

        class_types = self._get_defined_class_types()

        # add triples starting from each namespaces
        for _namespace in self.namespaces.values():

            classes = _namespace["classes"]
            properties = _namespace["properties"]
            vocabs = _namespace["vocabs"]

            for class_obj in classes.values():
                class_obj._gen_rdf(g, class_types)

            for prop_obj in properties.values():
                if prop_obj.name == "spdxId":
                    # the @id field in RDF already fulfils the function of this field
                    continue
                prop_obj._gen_rdf(g)

            for vocab_obj in vocabs.values():
                vocab_obj._gen_rdf(g)

        ttl_file_name = path.join(self.args["out_dir"], "model.ttl")
        with safe_open(ttl_file_name, "w") as f:
            f.write(g.serialize(format="turtle"))

        jsonld_file_name = path.join(self.args["out_dir"], "model.jsonld")
        with safe_open(jsonld_file_name, "w") as f:
            f.write(g.serialize(format="json-ld", auto_compact=True))

        convert_spdx_owl_to_jsonld_context(jsonld_file_name, self.args["out_dir"])

    def gen_json_dump(self) -> None:
        with safe_open(path.join(self.args["out_dir"], "model_dump.json"), "w") as f:
            f.write(json.dumps(self.namespaces, default=spec_to_json_encoder))


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

            if _values != "none":  # "none" values are ignored
                self.metadata[_key] = _values
            elif _key == "SubclassOf": # ... except in denoting parent class
                self.metadata[_key] = "owl:Thing"

        # add all default metadata fields
        union_dict(self.metadata, metadata_defaults)

        # add id metadata
        self.metadata["id"] = f"{id_metadata_prefix}{self.namespace_name}/{self.name}"

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
        if getattr(self, "spec", None) is None:
            return Literal(entity)

        if ":" in entity:
            [_namespace, _entity] = re.split(r":", entity)
        else:
            namespace_and_entity = entity.lstrip('/').rsplit('/', 1)
            if len(namespace_and_entity) == 1:
                _entity = namespace_and_entity[0]
                _namespace = self.namespace_name
            else:
                [_namespace, _entity] = namespace_and_entity

        rdf_dict = self.spec.rdf_dict

        if _namespace not in rdf_dict:
            return Literal(entity)

        return rdf_dict[_namespace][_entity]


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
        format_pattern (dict): format specification of this entity
        ext_props (dict): restrictions on external properties for this entity
        license_name (str): license provided through SPDX-License-Identifier
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
            format_pattern: dict,
            ext_props: dict,
            license_name: str):

        super().__init__(
            spec,
            namespace_name,
            name,
            summary,
            description,
            license_name
        )
        self.format_pattern = dict()

        self.logger = logging.getLogger(self.__class__.__name__)
        self._extract_metadata(metadata)
        self._extract_properties(props)
        self._extract_format(format_pattern)
        self.ext_props = ext_props
        if ext_props:
            self.logger.warning("External property restrictions aren't yet handled properly, they are added to the "
                                "description of the class.")
            for ext_prop in self.ext_props:
                for value in ext_prop["values"]:
                    self.description += f"\nExternal property restriction on {ext_prop['name']}: {value['name']}: " \
                                        f"{' '.join(value['values'])}"

        if self.format_pattern:
            self.logger.warning("Format restrictions aren't yet handled properly, they are added to the "
                                "description of the class.")
            for name, value in self.format_pattern.items():
                self.description += f"\nFormat restriction: {name}: {value}"

    # TODO: handle ext_props in some way -- for now, silently ignored
    # TODO: add format_pattern to generated rdf in some way

    def _extract_format(self, format_list):
        for _dict in format_list:
            _key = _dict["name"]
            _values = _dict["values"]

            if _key in self.format_pattern:
                # report the error
                self.logger.error(f"{self.name}: Format key '{_key}' already exists")

            self.format_pattern[_key] = _values

    def _gen_md(self, env, args: dict) -> None:

        fname = path.join(
            args["out_dir"], self.namespace_name, "Classes", f"{self.name}.md"
        )

        template = env.get_template("class.md.j2")
        result = template.render({'__version__': __version__, 'args': args} | vars(self))

        with safe_open(fname, "w") as f:
            f.write(result)


    def _gen_rdf(self, g: rdflib.Graph, class_types: List[URIRef]) -> None:

        cur = URIRef(self.metadata["id"])

        g.add((cur, RDF.type, OWL["Class"]))
        g.add((cur, RDF.type, SH.NodeShape))

        subclass_of = self.metadata.get("SubclassOf", None)
        if subclass_of:
            g.add((cur, RDFS.subClassOf, self._gen_uri(subclass_of)))

        g.add((cur, RDFS.comment, Literal(self.description)))
        g.add((cur, NS0.term_status, Literal(self.metadata.get("Status"))))

        sh_class = URIRef("http://www.w3.org/ns/shacl#class")

        for prop_name, prop_value in self.properties.items():
            if prop_name == "spdxId":
                # the @id field in RDF already fulfils the function of this field
                continue
            property_uri = self._gen_uri(prop_name)
            property_type_uri = self._gen_uri(prop_value["type"])
            min_count: str = prop_value["minCount"]
            max_count: str = prop_value["maxCount"]

            restriction_node = BNode()
            g.add((restriction_node, SH.path, property_uri))
            if property_type_uri in class_types:
                g.add((restriction_node, sh_class, property_type_uri))
            else:
                g.add((restriction_node, SH.datatype, property_type_uri))
            g.add((restriction_node, SH.name, Literal(prop_name)))
            if min_count != "0":
                g.add((restriction_node, SH.minCount, Literal(int(min_count))))
            if max_count != "*":
                g.add((restriction_node, SH.maxCount, Literal(int(max_count))))

            g.add((cur, SH.property, restriction_node))

    def is_literal(self) -> bool:
        return len(self.properties) == 0 and "xsd:string" in self.metadata.get("SubclassOf", [])


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

    def _gen_md(self, env, args: dict) -> None:

        fname = path.join(
            args["out_dir"], self.namespace_name, "Properties", f"{self.name}.md"
        )

        template = env.get_template("property.md.j2")
        result = template.render({'__version__': __version__, 'args': args} | vars(self))

        with safe_open(fname, "w") as f:
            f.write(result)


    def _gen_rdf(self, g: rdflib.Graph) -> None:

        # self.spec.rdf_dict
        cur = URIRef(self.metadata["id"])

        # nature of property
        _nature = self.metadata.get("Nature", None)
        if _nature == "ObjectProperty":
            g.add((cur, RDF.type, OWL["ObjectProperty"]))
        elif _nature == "DataProperty":
            g.add((cur, RDF.type, OWL["DatatypeProperty"]))
        else:
            self.logger.error(f"Invalid Nature attribute in metadata `{_nature}`")

        _range = self.metadata.get("Range", None)
        if _range:
            g.add((cur, RDFS.range, self._gen_uri(_range)))

        _domain = self.metadata.get("Domain", [])
        if len(_domain) > 1:
            orNode = BNode()
            g.add((cur, SH["or"], orNode))
            first_node = BNode()
            g.add((orNode, RDF.first, first_node))
            g.add((orNode, RDF.rest, RDF.nil))
            for _val in _domain:
                g.add((first_node, RDFS.domain, self._gen_uri(_val)))
        else:
            for _val in _domain:
                g.add((cur, RDFS.domain, self._gen_uri(_val)))

        g.add((cur, RDFS.comment, Literal(self.description)))
        g.add((cur, NS0.term_status, Literal(self.metadata.get("Status"))))


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

    def _gen_md(self, env, args: dict) -> None:

        fname = path.join(
            args["out_dir"], self.namespace_name, "Vocabularies", f"{self.name}.md"
        )

        template = env.get_template("vocab.md.j2")
        result = template.render({'__version__': __version__, 'args': args} | vars(self))

        with safe_open(fname, "w") as f:
            f.write(result)

    def _gen_rdf(self, g: rdflib.Graph):

        cur = URIRef(self.metadata["id"])

        g.add((cur, RDFS.comment, Literal(self.description)))
        g.add((cur, NS0.term_status, Literal(self.metadata.get("Status"))))

        # add entries
        entries = set()
        for _entry, _desc in self.entries.items():
            uri = cur + "/" + _entry
            entries.add(uri)
            g.add((uri, RDF.type, OWL.NamedIndividual))
            g.add((uri, RDF.type, cur))

        EnumeratedClass(cur, entries, g)


def spec_to_json_encoder(spec_obj):
    if isinstance(spec_obj, SpecClass):
        return {"summary": spec_obj.summary,
                "description": spec_obj.description,
                "metadata": spec_obj.metadata,
                "properties": spec_obj.properties}
    if isinstance(spec_obj, SpecProperty):
        return {"summary": spec_obj.summary,
                "description": spec_obj.description,
                "metadata": spec_obj.metadata}
    if isinstance(spec_obj, SpecVocab):
        return {"summary": spec_obj.summary,
                "description": spec_obj.description,
                "metadata": spec_obj.metadata,
                "entries": spec_obj.entries}
    return spec_obj

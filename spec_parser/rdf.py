# saving the model as RDF

# SPDX-License-Identifier: Apache-2.0

import json
import logging
from pathlib import Path

from rdflib import (
    BNode,
    Graph,
    Literal,
    Namespace,
    URIRef,
)
from rdflib.collection import Collection
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SH, SKOS, XSD
from rdflib.tools.rdf2dot import rdf2dot

URI_BASE = "https://spdx.org/rdf/3.0.1/terms/"


def gen_rdf(model, outdir, cfg):
    p = Path(outdir) / "rdf"
    p.mkdir(exist_ok=True)

    ont, shapes = gen_rdf_ontology(model)
    for ext in [
        "hext",
        "json-ld",
        "longturtle",
        "n3",
        "nt",
        "pretty-xml",
        "trig",
        "ttl",
        "xml",
    ]:
        shapes.serialize(p / ("spdx-shapes." + ext), format=ext, encoding="utf-8")
        ont.serialize(p / ("spdx-ontology." + ext), format=ext, encoding="utf-8")

    ctx = jsonld_context(ont, shapes)
    fn = p / "spdx-context.jsonld"
    with fn.open("w") as f:
        json.dump(ctx, f, sort_keys=True, indent=2)

    p = Path(outdir) / "diagram"
    p.mkdir(exist_ok=True)
    with (p / "spdx-shapes.dot").open("w") as f:
        rdf2dot(shapes, f)

    with (p / "spdx-ontology.dot").open("w") as f:
        rdf2dot(ont, f)


def xsd_range(rng, propname):
    if rng.startswith("xsd:"):
        return URIRef("http://www.w3.org/2001/XMLSchema#" + rng[4:])

    logging.warning(f"Uknown namespace in range <{rng}> of property {propname}")
    return None


def gen_rdf_ontology(model):
    ont = Graph()
    shapes = Graph()

    ont.bind("spdx", Namespace(URI_BASE))
    shapes.bind("spdx", Namespace(URI_BASE))

    OMG_ANN = Namespace("https://www.omg.org/spec/Commons/AnnotationVocabulary/")
    ont.bind("omg-ann", OMG_ANN)
    shapes.bind("omg-ann", OMG_ANN)

    def add_base(g):
        node = URIRef(URI_BASE)
        g.add((node, RDF.type, OWL.Ontology))
        g.add((node, OWL.versionIRI, node))
        g.add(
            (
                node,
                RDFS.label,
                Literal("System Package Data Exchange (SPDX) Ontology", lang="en"),
            )
        )
        g.add(
            (
                node,
                DCTERMS.abstract,
                Literal(
                    "This ontology defines the terms and relationships used in the SPDX specification to describe system packages",
                    lang="en",
                ),
            ),
        )
        g.add((node, DCTERMS.created, Literal("2024-04-05", datatype=XSD.date)))
        g.add((node, DCTERMS.creator, Literal("SPDX Project", lang="en")))
        g.add(
            (
                node,
                DCTERMS.license,
                URIRef("https://spdx.org/licenses/Community-Spec-1.0.html"),
            )
        )
        g.add((node, DCTERMS.references, URIRef("https://spdx.dev/specifications/")))
        g.add(
            (
                node,
                DCTERMS.title,
                Literal("System Package Data Exchange (SPDX) Ontology", lang="en"),
            )
        )
        g.add(
            (
                node,
                OMG_ANN.copyright,
                Literal("Copyright (C) 2024 SPDX Project", lang="en"),
            )
        )

    add_base(ont)
    add_base(shapes)

    gen_rdf_classes(model, ont, shapes)
    gen_rdf_properties(model, ont, shapes)
    #     gen_rdf_datatypes(model, g)
    gen_rdf_vocabularies(model, ont, shapes)
    gen_rdf_individuals(model, ont, shapes)

    return ont, shapes


def gen_rdf_classes(model, ont, shapes):
    AbstractClass = URIRef("http://spdx.invalid./AbstractClass")
    ont.add((AbstractClass, RDF.type, OWL.Class))

    for c in model.classes.values():
        node = URIRef(c.iri)
        ont.add((node, RDF.type, OWL.Class))
        if c.summary:
            ont.add((node, RDFS.comment, Literal(c.summary, lang="en")))
        parent = c.metadata.get("SubclassOf")
        if parent:
            pns = "" if parent.startswith("/") else f"/{c.ns.name}/"
            p = model.classes[pns + parent]
            ont.add((node, RDFS.subClassOf, URIRef(p.iri)))
        if c.metadata["Instantiability"] == "Abstract":
            ont.add((node, RDF.type, AbstractClass))

        if "spdxId" in c.all_properties:
            shapes.add((node, SH.nodeKind, SH.IRI))
        else:
            shapes.add((node, SH.nodeKind, SH.BlankNode))

        if c.properties:
            shapes.add((node, RDF.type, SH.NodeShape))
            for p in c.properties:
                fqprop = c.properties[p]["fqname"]
                if fqprop == "/Core/spdxId":
                    continue
                bnode = BNode()
                shapes.add((node, SH.property, bnode))
                prop = model.properties[fqprop]
                shapes.add((bnode, SH.path, URIRef(prop.iri)))
                prop_rng = prop.metadata["Range"]
                if ":" not in prop_rng:
                    typename = "" if prop_rng.startswith("/") else f"/{prop.ns.name}/"
                    typename += prop_rng
                else:
                    typename = prop_rng
                if typename in model.classes:
                    dt = model.classes[typename]
                    shapes.add((bnode, SH["class"], URIRef(dt.iri)))
                    if "spdxId" in dt.all_properties:
                        shapes.add((bnode, SH.nodeKind, SH.IRI))
                    else:
                        shapes.add((bnode, SH.nodeKind, SH.BlankNodeOrIRI))
                elif typename in model.vocabularies:
                    dt = model.vocabularies[typename]
                    shapes.add((bnode, SH["class"], URIRef(dt.iri)))
                    shapes.add((bnode, SH.nodeKind, SH.IRI))
                    lst = Collection(shapes, None)
                    for e in dt.entries:
                        lst.append(URIRef(dt.iri + "/" + e))
                    shapes.add((bnode, SH["in"], lst.uri))
                elif typename in model.datatypes:
                    dt = model.datatypes[typename]
                    if "pattern" in dt.format:
                        shapes.add((bnode, SH.pattern, Literal(dt.format["pattern"])))
                    t = xsd_range(dt.metadata["SubclassOf"], prop.iri)
                    if t:
                        shapes.add((bnode, SH.datatype, t))
                        shapes.add((bnode, SH.nodeKind, SH.Literal))
                else:
                    t = xsd_range(typename, prop.iri)
                    if t:
                        shapes.add((bnode, SH.datatype, t))
                        shapes.add((bnode, SH.nodeKind, SH.Literal))
                mincount = c.properties[p]["minCount"]
                if int(mincount) != 0:
                    shapes.add((bnode, SH.minCount, Literal(int(mincount))))
                maxcount = c.properties[p]["maxCount"]
                if maxcount != "*":
                    shapes.add((bnode, SH.maxCount, Literal(int(maxcount))))


def gen_rdf_properties(model, ont, shapes):
    for fqname, p in model.properties.items():
        if fqname == "/Core/spdxId":
            continue
        node = URIRef(p.iri)
        if p.summary:
            ont.add((node, RDFS.comment, Literal(p.summary, lang="en")))
        if p.metadata["Nature"] == "ObjectProperty":
            ont.add((node, RDF.type, OWL.ObjectProperty))
        # to add: ont.add((node, RDFS.domain, xxx))
        elif p.metadata["Nature"] == "DataProperty":
            ont.add((node, RDF.type, OWL.DatatypeProperty))
        rng = p.metadata["Range"]
        if ":" in rng:
            t = xsd_range(rng, p.name)
            if t:
                ont.add((node, RDFS.range, t))
        else:
            typename = "" if rng.startswith("/") else f"/{p.ns.name}/"
            typename += rng
            if typename in model.datatypes:
                t = xsd_range(model.datatypes[typename].metadata["SubclassOf"], p.name)
                if t:
                    ont.add((node, RDFS.range, t))
            else:
                dt = model.types[typename]
                ont.add((node, RDFS.range, URIRef(dt.iri)))


def gen_rdf_vocabularies(model, ont, shapes):
    for v in model.vocabularies.values():
        node = URIRef(v.iri)
        ont.add((node, RDF.type, OWL.Class))
        if v.summary:
            ont.add((node, RDFS.comment, Literal(v.summary, lang="en")))
        for e, d in v.entries.items():
            enode = URIRef(v.iri + "/" + e)
            ont.add((enode, RDF.type, OWL.NamedIndividual))
            ont.add((enode, RDF.type, node))
            ont.add((enode, RDFS.label, Literal(e)))
            ont.add((enode, RDFS.comment, Literal(d, lang="en")))


def gen_rdf_individuals(model, ont, shapes):
    for i in model.individuals.values():
        node = URIRef(i.iri)
        ont.add((node, RDF.type, OWL.NamedIndividual))
        if i.summary:
            ont.add((node, RDFS.comment, Literal(i.summary, lang="en")))
        typ = i.metadata["type"]
        typename = "" if typ.startswith("/") else f"/{i.ns.name}/"
        typename += typ
        dt = model.types[typename]
        ont.add((node, RDF.type, URIRef(dt.iri)))
        custom_iri = i.metadata.get("IRI")
        if custom_iri and custom_iri != i.iri:
            ont.add((node, OWL.sameAs, URIRef(custom_iri)))


def jsonld_context(ont, shapes):
    terms = dict()

    def get_subject_term(subject):
        if (subject, RDF.type, OWL.ObjectProperty) in ont:
            for _, _, o in ont.triples((subject, RDFS.range, None)):
                if o in vocab_classes:
                    return {
                        "@id": subject,
                        "@type": "@vocab",
                        "@context": {
                            "@vocab": o + "/",
                        },
                    }
                elif (o, RDF.type, OWL.Class) in ont:
                    return {
                        "@id": subject,
                        "@type": "@vocab",
                    }
        elif (subject, RDF.type, OWL.DatatypeProperty) in ont:
            for _, _, o in ont.triples((subject, RDFS.range, None)):
                return {
                    "@id": subject,
                    "@type": o,
                }

        return subject

    vocab_named_individuals = set()
    vocab_classes = set()
    for lst in shapes.objects(None, SH["in"]):
        c = Collection(shapes, lst)
        for e in c:
            vocab_named_individuals.add(e)
            for typ in ont.objects(e, RDF.type):
                if typ == OWL.NamedIndividual:
                    continue
                vocab_classes.add(typ)

    for subject in sorted(ont.subjects(unique=True)):
        # Skip named individuals in vocabularies
        if (
            subject,
            RDF.type,
            OWL.NamedIndividual,
        ) in ont and subject in vocab_named_individuals:
            continue

        try:
            base, ns, name = str(subject).rsplit("/", 2)
        except ValueError:
            continue

        if base != URI_BASE.rstrip("/"):
            continue

        key = name if ns == "Core" else ns.lower() + "_" + name

        if key in terms:
            current = terms[key]["@id"] if isinstance(terms[key], dict) else terms[key]
            logging.error(
                f"ERROR: Duplicate context key '{key}' for '{subject}'. Already mapped to '{current}'"
            )
            continue

        terms[key] = get_subject_term(subject)

    terms["spdx"] = URI_BASE
    terms["spdxId"] = "@id"
    terms["type"] = "@type"

    return {"@context": terms}

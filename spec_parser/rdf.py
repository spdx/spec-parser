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

CREATION_DATETIME = "2024-09-13T00:00:00Z"
SPDX_VERSION = "3.0.1"
URI_BASE = f"https://spdx.org/rdf/{SPDX_VERSION}/terms/"


def gen_rdf(model, outdir, cfg):
    p = Path(outdir) / "rdf"
    p.mkdir()

    ret = gen_rdf_ontology(model)
    for ext in ["hext", "json-ld", "longturtle", "n3", "nt", "pretty-xml", "trig", "ttl", "xml"]:
        f = p / ("spdx-model." + ext)
        ret.serialize(f, format=ext, encoding="utf-8")

    ctx = jsonld_context(ret)
    fn = p / "spdx-context.jsonld"
    with fn.open("w") as f:
        json.dump(ctx, f, sort_keys=True, indent=2)

    p = Path(outdir) / "diagram"
    p.mkdir(exist_ok=True)
    fn = p / "spdx-model.dot"
    with fn.open("w") as f:
        rdf2dot(ret, f)


def xsd_range(rng, propname):
    if rng.startswith("xsd:"):
        return URIRef("http://www.w3.org/2001/XMLSchema#" + rng[4:])

    logging.warning(f"Uknown namespace in range <{rng}> of property {propname}")
    return None


def gen_rdf_ontology(model):
    g = Graph()
    g.bind("spdx", Namespace(URI_BASE))
    OMG_ANN = Namespace("https://www.omg.org/spec/Commons/AnnotationVocabulary/")
    g.bind("omg-ann", OMG_ANN)

    node = URIRef(URI_BASE)
    g.add((node, RDF.type, OWL.Ontology))
    g.add((node, OWL.versionIRI, node))
    g.add((node, RDFS.label, Literal("System Package Data Exchange (SPDX) Ontology", lang="en")))
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
    g.add((node, DCTERMS.license, URIRef("https://spdx.org/licenses/Community-Spec-1.0.html")))
    g.add((node, DCTERMS.references, URIRef("https://spdx.dev/specifications/")))
    g.add((node, DCTERMS.title, Literal("System Package Data Exchange (SPDX) Ontology", lang="en")))
    g.add((node, OMG_ANN.copyright, Literal("Copyright (C) 2024 SPDX Project", lang="en")))

    gen_rdf_classes(model, g)
    gen_rdf_properties(model, g)
    #     gen_rdf_datatypes(model, g)
    gen_rdf_vocabularies(model, g)
    gen_rdf_individuals(model, g)

    return g


def gen_rdf_classes(model, g):
    AbstractClass = URIRef("http://spdx.invalid./AbstractClass")
    g.add((AbstractClass, RDF.type, OWL.Class))

    for c in model.classes.values():
        node = URIRef(c.iri)
        g.add((node, RDF.type, OWL.Class))
        if c.summary:
            g.add((node, RDFS.comment, Literal(c.summary, lang="en")))
        parent = c.metadata.get("SubclassOf")
        if parent:
            pns = "" if parent.startswith("/") else f"/{c.ns.name}/"
            p = model.classes[pns + parent]
            g.add((node, RDFS.subClassOf, URIRef(p.iri)))
        if c.metadata["Instantiability"] == "Abstract":
            g.add((node, RDF.type, AbstractClass))

        if "spdxId" in c.all_properties:
            g.add((node, SH.nodeKind, SH.IRI))
        else:
            g.add((node, SH.nodeKind, SH.BlankNode))

        if c.properties:
            g.add((node, RDF.type, SH.NodeShape))
            for p in c.properties:
                fqprop = c.properties[p]["fqname"]
                if fqprop == "/Core/spdxId":
                    continue
                bnode = BNode()
                g.add((node, SH.property, bnode))
                prop = model.properties[fqprop]
                g.add((bnode, SH.path, URIRef(prop.iri)))
                prop_rng = prop.metadata["Range"]
                if ":" not in prop_rng:
                    typename = "" if prop_rng.startswith("/") else f"/{prop.ns.name}/"
                    typename += prop_rng
                else:
                    typename = prop_rng
                if typename in model.classes:
                    dt = model.classes[typename]
                    g.add((bnode, SH["class"], URIRef(dt.iri)))
                    if "spdxId" in dt.all_properties:
                        g.add((bnode, SH.nodeKind, SH.IRI))
                    else:
                        g.add((bnode, SH.nodeKind, SH.BlankNodeOrIRI))
                elif typename in model.vocabularies:
                    dt = model.vocabularies[typename]
                    g.add((bnode, SH["class"], URIRef(dt.iri)))
                    g.add((bnode, SH.nodeKind, SH.IRI))
                    lst = Collection(g, None)
                    for e in dt.entries:
                        lst.append(URIRef(dt.iri + "/" + e))
                    g.add((bnode, SH["in"], lst.uri))
                elif typename in model.datatypes:
                    dt = model.datatypes[typename]
                    if "pattern" in dt.format:
                        g.add((bnode, SH.pattern, Literal(dt.format["pattern"])))
                    t = xsd_range(dt.metadata["SubclassOf"], prop.iri)
                    if t:
                        g.add((bnode, SH.datatype, t))
                        g.add((bnode, SH.nodeKind, SH.Literal))
                else:
                    t = xsd_range(typename, prop.iri)
                    if t:
                        g.add((bnode, SH.datatype, t))
                        g.add((bnode, SH.nodeKind, SH.Literal))
                mincount = c.properties[p]["minCount"]
                if int(mincount) != 0:
                    g.add((bnode, SH.minCount, Literal(int(mincount))))
                maxcount = c.properties[p]["maxCount"]
                if maxcount != "*":
                    g.add((bnode, SH.maxCount, Literal(int(maxcount))))


def gen_rdf_properties(model, g):
    for fqname, p in model.properties.items():
        if fqname == "/Core/spdxId":
            continue
        node = URIRef(p.iri)
        if p.summary:
            g.add((node, RDFS.comment, Literal(p.summary, lang="en")))
        if p.metadata["Nature"] == "ObjectProperty":
            g.add((node, RDF.type, OWL.ObjectProperty))
        # to add: g.add((node, RDFS.domain, xxx))
        elif p.metadata["Nature"] == "DataProperty":
            g.add((node, RDF.type, OWL.DatatypeProperty))
        rng = p.metadata["Range"]
        if ":" in rng:
            t = xsd_range(rng, p.name)
            if t:
                g.add((node, RDFS.range, t))
        else:
            typename = "" if rng.startswith("/") else f"/{p.ns.name}/"
            typename += rng
            if typename in model.datatypes:
                t = xsd_range(model.datatypes[typename].metadata["SubclassOf"], p.name)
                if t:
                    g.add((node, RDFS.range, t))
            else:
                dt = model.types[typename]
                g.add((node, RDFS.range, URIRef(dt.iri)))


def gen_rdf_vocabularies(model, g):
    for v in model.vocabularies.values():
        node = URIRef(v.iri)
        g.add((node, RDF.type, OWL.Class))
        if v.summary:
            g.add((node, RDFS.comment, Literal(v.summary, lang="en")))
        for e, d in v.entries.items():
            enode = URIRef(v.iri + "/" + e)
            g.add((enode, RDF.type, OWL.NamedIndividual))
            g.add((enode, RDF.type, node))
            g.add((enode, RDFS.label, Literal(e)))
            g.add((enode, RDFS.comment, Literal(d, lang="en")))


def gen_rdf_individuals(model, g):
    class SPDX:
        """SPDX terms"""

        CreationInfo = URIRef(URI_BASE + "Core/CreationInfo")
        creationInfo = URIRef(URI_BASE + "Core/creationInfo")
        created = URIRef(URI_BASE + "Core/created")
        createdBy = URIRef(URI_BASE + "Core/createdBy")
        spdxId = URIRef(URI_BASE + "Core/spdxId")
        SpdxOrganization = URIRef("https://spdx.org/")
        specVersion = URIRef(URI_BASE + "Core/specVersion")

    # Define an instance of CreationInfo as a blank node
    creation_info = BNode("_CreationInfo")
    g.add((creation_info, RDF.type, SPDX.CreationInfo))
    g.add((creation_info, SPDX.created, Literal(CREATION_DATETIME, datatype=XSD.dateTimeStamp)))
    g.add((creation_info, SPDX.createdBy, SPDX.SpdxOrganization))
    g.add((creation_info, SPDX.specVersion, Literal(SPDX_VERSION, datatype=XSD.string)))

    # Add all individuals
    for i in model.individuals.values():
        node = URIRef(i.iri)
        g.add((node, RDF.type, OWL.NamedIndividual))
        if i.summary:
            g.add((node, RDFS.comment, Literal(i.summary, lang="en")))
        typ = i.metadata["type"]
        typename = "" if typ.startswith("/") else f"/{i.ns.name}/"
        typename += typ
        dt = model.types[typename]
        g.add((node, RDF.type, URIRef(dt.iri)))
        custom_iri = i.metadata.get("IRI")
        if custom_iri and custom_iri != i.iri:
            g.add((node, OWL.sameAs, URIRef(custom_iri)))
        g.add((node, SPDX.creationInfo, creation_info))


def jsonld_context(g):
    terms = dict()

    def get_subject_term(subject):
        if (subject, RDF.type, OWL.ObjectProperty) in g:
            for _, _, o in g.triples((subject, RDFS.range, None)):
                if o in vocab_classes:
                    return {
                        "@id": subject,
                        "@type": "@vocab",
                        "@context": {
                            "@vocab": o + "/",
                        },
                    }
                elif (o, RDF.type, OWL.Class) in g:
                    return {
                        "@id": subject,
                        "@type": "@vocab",
                    }
        elif (subject, RDF.type, OWL.DatatypeProperty) in g:
            for _, _, o in g.triples((subject, RDFS.range, None)):
                return {
                    "@id": subject,
                    "@type": o,
                }

        return subject

    vocab_named_individuals = set()
    vocab_classes = set()
    for lst in g.objects(None, SH["in"]):
        c = Collection(g, lst)
        for e in c:
            vocab_named_individuals.add(e)
            for typ in g.objects(e, RDF.type):
                if typ == OWL.NamedIndividual:
                    continue
                vocab_classes.add(typ)

    for subject in sorted(g.subjects(unique=True)):
        # Skip named individuals in vocabularies
        if (subject, RDF.type, OWL.NamedIndividual) in g and subject in vocab_named_individuals:
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
            logging.error(f"ERROR: Duplicate context key '{key}' for '{subject}'. Already mapped to '{current}'")
            continue

        terms[key] = get_subject_term(subject)

    terms["spdx"] = URI_BASE
    terms["spdxId"] = "@id"
    terms["type"] = "@type"

    return {"@context": terms}

# saving the model as RDF

# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
from types import new_class

from rdflib import (
    Graph,
    Literal,
    Namespace,
    URIRef,
)
from rdflib.namespace import (
    DOAP, OWL, RDF, RDFS, SH, SKOS, XSD,
)
from rdflib.tools.rdf2dot import (
    rdf2dot
)

from owlready2 import (
    get_namespace,
    get_ontology,
    ConstrainedDatatype
)

URI_BASE = 'https://rdf.spdx.org/v3/'

def gen_rdf(model, dir, cfg):
    p = Path(dir)
    p.mkdir(exist_ok=True)

    ret = gen_rdf_ontology(model)
    for ext in ["xml", "ttl", "pretty-xml", "json-ld"]:
        f = p / ("ontology.rdf." + ext)
        ret.serialize(f, format=ext, encoding="utf-8")
    fn = p / "ontology.rdf.dot"
    with open(fn, "w") as f:
        rdf2dot(ret, f)
 
    ret = gen_owl_ontology(model)
    for ext in ["rdfxml", "ntriples"]:
        fn = p / ("ontology.owl." + ext)
        with open(fn, "wb") as f:
            ret.save(f, format=ext)


def gen_rdf_ontology(model):
    g = Graph()
    g.bind("spdx", Namespace(URI_BASE))
    g.bind("xsd", XSD)

    node = URIRef(URI_BASE)
    g.add((node, RDF.type, OWL.Ontology))
    g.add((node, OWL.versionIRI, node))

    for fqname, c in model.classes.items():
        node = URIRef(c.iri)
        g.add((node, RDF.type, RDFS.Class))
        g.add((node, RDF.type, OWL.Class))
        if c.summary:
            g.add((node, RDFS.comment, Literal(c.summary, lang='en')))
        parent = c.metadata.get("SubclassOf")
        if parent:
            p = model.classes[parent]
            g.add((node, RDFS.subClassOf, URIRef(p.iri)))
        if c.properties:
            shapenode = URIRef(c.iri + 'Shape')
            g.add((shapenode, RDF.type, SH.NodeShape))

    for fqname, p in model.properties.items():
        node = URIRef(p.iri)
        g.add((node, RDF.type, RDF.Property))
        if p.summary:
            g.add((node, RDFS.comment, Literal(p.summary, lang='en')))
        if p.metadata["Nature"] == "ObjectProperty":
            g.add((node, RDF.type, OWL.ObjectProperty))
#             g.add((node, RDFS.domain, xxx))
        elif p.metadata["Nature"] == "DataProperty":
            g.add((node, RDF.type, OWL.DatatypeProperty))
        rng = p.metadata["Range"]
        if ':' in rng:
            if rng.startswith('xsd:'):
                t = URIRef("http://www.w3.org/2001/XMLSchema#"+rng[4:])
                g.add((node, RDFS.range, t))
            else:
                logging.warn(f'Uknown namespace in range <{rng}> of property {p.name}')
        else:
            pass
#                 dt = model.classes[rng]
#                 g.add((node, RDFS.range, URIRef(dt.iri)))

    for fqname, v in model.vocabularies.items():
        node = URIRef(v.iri)
        g.add((node, RDF.type, RDFS.Class))
        g.add((node, RDF.type, OWL.Class))
        if v.summary:
            g.add((node, RDFS.comment, Literal(v.summary, lang='en')))
        for e, d in v.entries.items():
            enode = URIRef(v.iri + '/' + e)
            g.add((enode, RDF.type, node))
            g.add((enode, RDFS.label, Literal(e)))
            g.add((enode, RDFS.comment, Literal(d, lang='en')))

    return g




def gen_owl_ontology(model):
    spdx_ontology = get_ontology(URI_BASE)
    with spdx_ontology:
        for ns in model.namespaces:
            _ = get_namespace(ns.iri)

    for fqname, c in model.classes.items():
            nc = new_class(c.name)
            nc.namespace = c.ns.iri
#            nc = new_class("NewClassName", (SuperClass,))
            pass
    return spdx_ontology

'''
# A new property can be created by sublcassing the ObjectProperty or DataProperty class.
# The ‘domain’ and ‘range’ properties can be used to specify.
# Domain and range must be given in list
Property.min(cardinality, Range_Class)
Property.max(cardinality, Range_Class)
foo = ConstrainedDatatype(str, pattern = xxx)
'''

# TODO :-D
def gen_jsonld_context(): pass
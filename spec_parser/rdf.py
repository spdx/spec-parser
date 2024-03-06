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
from rdflib.namespace import (
    OWL, RDF, RDFS, SH, XSD,
)
from rdflib.tools.rdf2dot import (
    rdf2dot
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
    ctx = jsonld_context(ret)
    fn = p / "context.jsonld"
    with open(fn, "w") as f:
        json.dump(ctx, f, sort_keys=True, indent=2)



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
            pns = "" if parent.startswith("/") else f"/{c.ns.name}/"
            p = model.classes[pns+parent]
            g.add((node, RDFS.subClassOf, URIRef(p.iri)))
        if c.properties:
            g.add((node, RDF.type, SH.NodeShape))
            for p in c.properties:
                fqprop = c.properties[p]["fqname"]
                prop = model.properties[fqprop]
                if prop.metadata["Nature"] == "IdProperty":
                    continue

                bnode = BNode()
                g.add((node, SH.property, bnode))
                fqprop = c.properties[p]["fqname"]
                g.add((bnode, SH.path, URIRef(model.properties[fqprop].iri)))
                mincount = c.properties[p]["minCount"]
                if int(mincount) != 0:
                    g.add((bnode, SH.minCount, Literal(int(mincount))))
                maxcount = c.properties[p]["maxCount"]
                if maxcount != '*':
                    g.add((bnode, SH.maxCount, Literal(int(maxcount))))


    for fqname, p in model.properties.items():
        if p.metadata["Nature"] == "IdProperty":
            continue
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
            typename = "" if rng.startswith("/") else f"/{p.ns.name}/"
            typename += rng
            dt = model.types[typename]
            g.add((node, RDFS.range, URIRef(dt.iri)))
            
    for fqname, v in model.vocabularies.items():
        node = URIRef(v.iri)
        g.add((node, RDF.type, RDFS.Class))
        g.add((node, RDF.type, OWL.Class))
        if v.summary:
            g.add((node, RDFS.comment, Literal(v.summary, lang='en')))
        for e, d in v.entries.items():
            enode = URIRef(v.iri + '/' + e)
            g.add((enode, RDF.type, OWL.NamedIndividual))
            g.add((enode, RDF.type, node))
            g.add((enode, RDFS.label, Literal(e)))
            g.add((enode, RDFS.comment, Literal(d, lang='en')))

    for fqname, i in model.individuals.items():
        node = URIRef(i.iri)
        g.add((node, RDF.type, OWL.NamedIndividual))
        if i.summary:
            g.add((node, RDFS.comment, Literal(i.summary, lang='en')))
        typ = i.metadata["type"]
        typename = "" if typ.startswith("/") else f"/{i.ns.name}/"
        typename += typ
        dt = model.types[typename]
        g.add((node, RDFS.range, URIRef(dt.iri)))
        custom_iri = i.metadata.get("IRI")
        if custom_iri:
            g.add((node, OWL.sameAs, URIRef(custom_iri)))

    return g



def jsonld_context(g):
    terms = dict()
    terms['spdx'] = URI_BASE
    for s in g.subjects(unique=True):
        s = str(s)
        if s.startswith(URI_BASE):
            short = s[len(URI_BASE):]
            if short:
                terms[short] = 'spdx:' + short
    return {'@context': terms}

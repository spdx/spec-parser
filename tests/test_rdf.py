# SPDX-FileCopyrightText: 2026-present SPDX Contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

import logging
from types import SimpleNamespace

import pytest
from rdflib import Graph, Literal, URIRef

from spec_parser.model import Model
from spec_parser.rdf import URI_BASE, gen_rdf_individuals

CORE = URI_BASE + "Core/"
CREATED = "2024-11-22T03:00:01Z"
DATETIME = r"^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])T(([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]|23:59:60)Z$"
VERSION = r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))?$"
META = {"specVersion": "3.0.1", "created": CREATED, "createdBy": "/Core/SpdxOrganization"}  # valid


def individual(name, typ, **meta):
    ns = SimpleNamespace
    return ns(name=name, fqname=f"/Core/{name}", iri=CORE + name, summary=None, metadata={"type": typ, **meta}, ns=ns(name="Core"))


def rdf_model(name, **meta):
    ns = SimpleNamespace
    inds = [individual("SpdxOrganization", "T", **META), individual(name, "T", **meta)]
    return ns(individuals={i.fqname: i for i in inds}, types={"/Core/T": ns(iri=CORE + "T")})


def checked_model(**meta):
    ns = SimpleNamespace
    core = ns(name="Core")
    m = Model()
    m.classes = {f"/Core/{c}": ns(fqsupercname=p) for c, p in [
        ("Element", None), ("Agent", "/Core/Element"), ("Organization", "/Core/Agent"), ("IndividualElement", "/Core/Element"),
    ]}
    m.properties = {
        "/Core/created": ns(ns=core, metadata={"Range": "DateTime"}),
        "/Core/specVersion": ns(ns=core, metadata={"Range": "VersionNumber"}),
    }
    m.datatypes = {
        "/Core/DateTime": ns(format={"pattern": DATETIME}),
        "/Core/VersionNumber": ns(format={"pattern": VERSION}),
    }
    inds = [
        individual("SpdxOrganization", "Organization", **META),
        individual("NoneElement", "IndividualElement", **META),
        individual("X", "IndividualElement", **meta),
    ]
    m.individuals = {i.fqname: i for i in inds}
    m.check_individuals_creation_info()
    return m


def errors(caplog):
    return [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]


# RDF output

@pytest.mark.parametrize(("name", "version"), [("NoneElement", "3.0.1"), ("RedactedElement", "3.1")])
def test_creation_info_from_metadata(name, version):
    g = Graph()
    gen_rdf_individuals(rdf_model(name, **{**META, "specVersion": version}), g)
    ci = g.value(URIRef(CORE + name), URIRef(CORE + "creationInfo"))
    assert ci == URIRef(f"https://spdx.org/rdf/{version}/creationInfo_{name}")
    assert g.value(ci, URIRef(CORE + "specVersion")) == Literal(version)
    assert str(g.value(ci, URIRef(CORE + "created"))) == CREATED
    assert g.value(ci, URIRef(CORE + "createdBy")) == URIRef(CORE + "SpdxOrganization")


def test_missing_metadata_skipped_in_rdf(caplog):
    g = Graph()
    gen_rdf_individuals(rdf_model("NewIndividual", specVersion="3.1"), g)
    assert "NewIndividual" in caplog.text
    assert not list(g.triples((URIRef(CORE + "NewIndividual"), None, None)))


# metadata checks

@pytest.mark.parametrize(("spec_version", "created"), [
    ("3.0", CREATED),
    ("3.0.1", CREATED),
    ("3.1", CREATED),
    ("3.0.1", "2016-12-31T23:59:60Z"),  # leap second
])
def test_valid_creation_info(caplog, spec_version, created):
    checked_model(**{**META, "specVersion": spec_version, "created": created})
    assert errors(caplog) == []


@pytest.mark.parametrize(("key", "value"), [
    *[("created", v) for v in [
        "2024-11-22", "2024-11-22T03:00:01", "2024-11-22T03:00:01+00:00", "2024-11-22T03:00:01.5Z",
        "2024-13-22T03:00:01Z", "2024-11-22T24:00:00Z", "2024-11-22T03:00:01Z\n",
    ]],
    *[("specVersion", v) for v in ["3", "v3.1", "03.1", "3.1.0-rc1", "3.1.", "3.1\n"]],
    # unqualified, unknown, not an Agent, an IRI
    *[("createdBy", v) for v in ["SpdxOrganization", "/Core/Unknown", "/Core/NoneElement", "https://spdx.org/"]],
])
def test_invalid_creation_info(caplog, key, value):
    checked_model(**{**META, key: value})
    assert any(f"invalid {key}" in e for e in errors(caplog))


@pytest.mark.parametrize("key", ["specVersion", "created", "createdBy"])
def test_missing_creation_info(caplog, key):
    checked_model(**{k: v for k, v in META.items() if k != key})
    assert any(f"missing required metadata '{key}'" in e for e in errors(caplog))

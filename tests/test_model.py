# SPDX-FileCopyrightText: 2026-present SPDX Contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

import logging
from types import SimpleNamespace

import pytest

from spec_parser.model import Model

DATETIME = r"^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])T(([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]|23:59:60)Z$"
VERSION = r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))?$"


def model_with(**meta):
    core = SimpleNamespace(name="Core")
    m = Model()
    m.properties = {
        "/Core/created": SimpleNamespace(ns=core, metadata={"Range": "DateTime"}),
        "/Core/specVersion": SimpleNamespace(
            ns=core, metadata={"Range": "VersionNumber"}
        ),
    }
    m.datatypes = {
        "/Core/DateTime": SimpleNamespace(format={"pattern": DATETIME}),
        "/Core/VersionNumber": SimpleNamespace(format={"pattern": VERSION}),
    }
    m.individuals = {"/Core/X": SimpleNamespace(fqname="/Core/X", metadata=meta)}
    return m


def errors(caplog):
    return [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]


@pytest.mark.parametrize("spec_version", ["3.0", "3.0.1", "3.1"])
def test_valid_spec_version(caplog, spec_version):
    model_with(
        specVersion=spec_version, created="2024-11-22T03:00:01Z"
    ).check_individuals_creation_info()
    assert errors(caplog) == []


@pytest.mark.parametrize(
    "created",
    [
        "2024-11-22T03:00:01Z",
        "2016-12-31T23:59:60Z",  # leap second
    ],
)
def test_valid_created(caplog, created):
    model_with(specVersion="3.0.1", created=created).check_individuals_creation_info()
    assert errors(caplog) == []


@pytest.mark.parametrize(
    "created",
    [
        "2024-11-22",
        "2024-11-22T03:00:01",
        "2024-11-22T03:00:01+00:00",
        "2024-11-22T03:00:01.5Z",
        "2024-13-22T03:00:01Z",
        "2024-11-22T24:00:00Z",
        "2024-11-22T03:00:01Z\n",
    ],
)
def test_invalid_created(caplog, created):
    model_with(specVersion="3.0.1", created=created).check_individuals_creation_info()
    assert any("invalid created" in e for e in errors(caplog))


@pytest.mark.parametrize(
    "spec_version", ["3", "v3.1", "03.1", "3.1.0-rc1", "3.1.", "3.1\n"]
)
def test_invalid_spec_version(caplog, spec_version):
    model_with(
        specVersion=spec_version, created="2024-11-22T03:00:01Z"
    ).check_individuals_creation_info()
    assert any("invalid specVersion" in e for e in errors(caplog))


def test_missing_creation_info(caplog):
    model_with(created="2024-11-22T03:00:01Z").check_individuals_creation_info()
    assert any("missing required metadata 'specVersion'" in e for e in errors(caplog))

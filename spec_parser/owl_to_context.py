# SPDX-FileCopyrightText: 2023 spdx contributors
#
# SPDX-License-Identifier: Apache-2.0
import json
from os import path

PROPERTIES_WITH_ENUM_RANGE = [
    "safetyRiskAssessment",
    "sensitivePersonalInformation",
    "annotationType",
    "externalIdentifierType",
    "externalReferenceType",
    "algorithm",
    "scope",
    "profile",
    "completeness",
    "relationshipType",
    "confidentialityLevel",
    "datasetAvailability",
    "decisionType",
    "justificationType",
    "catalogType",
    "conditionality",
    "sbomType",
    "softwareLinkage",
    "purpose",
]

REFERENCE_PROPERTY_TYPES = [
    "core:Element",
    "core:Agent",
]

LOCAL_PROFILE_CONTEXT = {
    "core": "https://spdx.org/rdf/Core/ProfileIdentifierType/core",
    "software": "https://spdx.org/rdf/Core/ProfileIdentifierType/software",
    "licensing": "https://spdx.org/rdf/Core/ProfileIdentifierType/licensing",
    "security": "https://spdx.org/rdf/Core/ProfileIdentifierType/security",
    "build": "https://spdx.org/rdf/Core/ProfileIdentifierType/build",
    "ai": "https://spdx.org/rdf/Core/ProfileIdentifierType/ai",
    "dataset": "https://spdx.org/rdf/Core/ProfileIdentifierType/dataset",
    "usage": "https://spdx.org/rdf/Core/ProfileIdentifierType/usage",
    "extension": "https://spdx.org/rdf/Core/ProfileIdentifierType/extension",
}


def convert_spdx_owl_to_jsonld_context(spdx_owl: str, out_dir: str):
    # spdx_owl must point to the OWL in json-ld format
    with open(spdx_owl, "r") as infile:
        owl_dict = json.load(infile)

    context_dict = owl_dict["@context"]

    for node in owl_dict["@graph"]:
        node_type = node.get("@type")
        if not node_type:
            continue

        if "owl:NamedIndividual" in node_type:
            continue

        node_id = node["@id"]
        name = get_name_from_node_id(node_id)

        if node_type in ["owl:DatatypeProperty", "owl:ObjectProperty"]:
            type_id = node["rdfs:range"]["@id"]

            if name in context_dict and context_dict[name]["@id"].startswith("core"):
                # if in doubt, prioritize core properties
                continue

            if name in PROPERTIES_WITH_ENUM_RANGE:
                if name == "profile":
                    # FIXME: since the allowed values for the profile enum collide with
                    # our namespaces, we need to explicitly remap their meaning in the context
                    local_context = LOCAL_PROFILE_CONTEXT
                else:
                    local_context = {"@vocab": type_id + "/"}

                node_context = {
                    "@id": node_id,
                    "@type": "@vocab",
                    "@context": local_context,
                }
            elif node_type == "owl:ObjectProperty" and type_id in REFERENCE_PROPERTY_TYPES:
                node_context = {"@id": node_id, "@type": "@id"}
            else:
                node_context = {"@id": node_id, "@type": type_id}

        elif node_type == "owl:Class" or isinstance(node_type, list):
            node_context = node_id

        else:
            print(f"unknown node_type: {node_type}")
            continue

        context_dict[name] = node_context

    context_dict["spdxId"] = "@id"
    context_dict["type"] = "@type"

    fname = path.join(out_dir, "context.json")
    with open(fname, "w") as f:
        json.dump(context_dict, f)


def get_name_from_node_id(node_id) -> str:
    return node_id.split(":")[-1]

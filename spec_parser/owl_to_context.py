# SPDX-FileCopyrightText: 2023 spdx contributors
#
# SPDX-License-Identifier: Apache-2.0
import json
from os import path

# We decided to not support inlining/embedding of Elements in JSON-LD.
# Instead, the spdxId has to used to reference Element objects.
# Properties with the following types therefore have to get "@type: @id" instead.
REFERENCE_PROPERTY_TYPES = [
    "core:Element",
    "core:Agent",
    "core:CreationInfo"
]

# Since the allowed values for the profile enum collide with
# the profile namespaces, we need to explicitly remap their meaning in the context.
PROFILE_LOCAL_CONTEXT = {
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

            # first check if the property range is an Enum (by checking for the "owl:oneOf" key)
            range_node_from_owl = get_range_node_from_owl(node, owl_dict)
            if range_node_from_owl and "owl:oneOf" in range_node_from_owl:
                if name == "profile":
                    local_context = PROFILE_LOCAL_CONTEXT
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
        json.dump({ "@context": context_dict}, f)


def get_name_from_node_id(node_id) -> str:
    return node_id.split(":")[-1]


def get_range_node_from_owl(node, owl_dict):
    range_node_id = node["rdfs:range"]["@id"]
    for owl_node in owl_dict["@graph"]:
        if owl_node["@id"] == range_node_id:
            return owl_node


# saving the model as a single Microsoft Word document

# SPDX-License-Identifier: Apache-2.0

import logging

from jinja2 import Environment, PackageLoader, select_autoescape

logger = logging.getLogger(__name__)


def gen_word(model, outpath, cfg):
    jinja = Environment(
        loader=PackageLoader("spec_parser", package_path="templates/word"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    jinja.globals = cfg.all_as_dict
    jinja.globals["show_name"] = show_name
    jinja.globals["ext_property_name"] = ext_property_name
    jinja.globals["not_none"] = lambda x: str(x) if x is not None else ""

    output_file = outpath / "model.md"
    p = outpath / "files"
    p.mkdir()

    for ns in model.namespaces:
        d = p / ns.name
        d.mkdir()
        f = d / f"{ns.name}.md"

        template = jinja.get_template("namespace.md.j2")
        page = template.render(vars(ns))
        f.write_text(page)

    def _generate_in_dir(dirname, group, tmplfname):
        for s in group.values():
            in_ns = s.ns
            d = p / in_ns.name / dirname
            d.mkdir(exist_ok=True)
            f = d / f"{s.name}.md"

            template = jinja.get_template(tmplfname)
            page = template.render(vars(s))
            f.write_text(page)

    _generate_in_dir("Classes", model.classes, "class.md.j2")
    _generate_in_dir("Properties", model.properties, "property.md.j2")
    _generate_in_dir("Vocabularies", model.vocabularies, "vocabulary.md.j2")
    _generate_in_dir("Individuals", model.individuals, "individual.md.j2")
    _generate_in_dir("Datatypes", model.datatypes, "datatype.md.j2")

    namespaces = [ns.name for ns in model.namespaces]

    def _add_content(f):
        with output_file.open("a", encoding="utf-8") as of:
            of.write(f.read_text(encoding="utf-8"))
            of.write("\n")

    def _add_string(s):
        with output_file.open("a", encoding="utf-8") as of:
            of.write(s)

    output_file.write_text(f"<-- {cfg.autogen_header} -->\n", encoding="utf-8")
    _add_string("<!-- SPDX-License-Identifier: Community-Spec-1.0 -->\n\n")

    # hardwired order of namespaces
    for nsname in [
        "Core",
        "Software",
        "Security",
        "Licensing",
        "SimpleLicensing",
        "ExpandedLicensing",
        "Dataset",
        "AI",
        "Build",
        "Lite",
        "Extension",
        "Hardware",
        "Service",
        "SupplyChain",
    ]:
        if nsname in namespaces:
            f = p / nsname / f"{nsname}.md"
            _add_content(f)
            for subdirname in ["Classes", "Properties", "Vocabularies", "Individuals", "Datatypes"]:
                subdir = p / nsname / subdirname
                if subdir.is_dir():
                    _add_string(f"## {subdirname}\n\n")
                    for f in sorted(subdir.glob("*.md")):
                        _add_content(f)
            namespaces.remove(nsname)

    if namespaces:
        logger.warning("The following namespaces were not processed for Word generation: %s", ", ".join(namespaces))


def show_name(name, *, showshort=False):
    if name.startswith("/"):
        _, other_ns, name = name.split("/")
        return name if showshort else f"/{other_ns}/{name}"
    else:
        return name


def ext_property_name(name):
    (_, pns, pclass, pname) = name.split("/")
    return f"{pname} from /{pns}/{pclass}"

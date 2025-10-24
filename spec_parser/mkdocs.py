# saving the model as MkDocs input

# SPDX-License-Identifier: Apache-2.0

import logging

from jinja2 import Environment, PackageLoader, select_autoescape

logger = logging.getLogger(__name__)

def gen_mkdocs(model, outpath, cfg):
    jinja = Environment(
        loader=PackageLoader("spec_parser", package_path="templates/mkdocs"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    jinja.globals = cfg.all_as_dict
    jinja.globals["class_link"] = class_link
    jinja.globals["property_link"] = property_link
    jinja.globals["ext_property_link"] = ext_property_link
    jinja.globals["type_link"] = lambda x, showshort=False: type_link(x, model, showshort=showshort)
    jinja.globals["not_none"] = lambda x: str(x) if x is not None else ""

    p = outpath

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

    def _gen_filelist(nsname, itemslist, heading):
        ret = []
        nameslist = [c.name for c in itemslist.values()]
        if nameslist:
            ret.append(f"    - {heading}:")
            ret.extend(f"      - '{n}': model/{nsname}/{heading}/{n}.md" for n in sorted(nameslist))
        return ret

    namespaces = [ns.name for ns in model.namespaces]
    files = dict()
    for ns in model.namespaces:
        nsn = ns.name
        files[nsn] = []
        files[nsn].append(f"  - {nsn}:")
        files[nsn].append(f"    - 'Description': model/{nsn}/{nsn}.md")
        files[nsn].extend(_gen_filelist(nsn, ns.classes, "Classes"))
        files[nsn].extend(_gen_filelist(nsn, ns.properties, "Properties"))
        files[nsn].extend(_gen_filelist(nsn, ns.vocabularies, "Vocabularies"))
        files[nsn].extend(_gen_filelist(nsn, ns.individuals, "Individuals"))
        files[nsn].extend(_gen_filelist(nsn, ns.datatypes, "Datatypes"))

    filelines = []
    filelines.append("- model:")
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
            filelines.extend(files[nsname])
            namespaces.remove(nsname)

    if namespaces:
        logger.warning("The following namespaces were not processed for MkDocs generation: %s", ", ".join(namespaces))

    fn = outpath / "model-files.yml"
    fn.write_text("\n".join(filelines))


def class_link(name):
    if name.startswith("/"):
        _, other_ns, name = name.split("/")
        return f"[/{other_ns}/{name}](../../{other_ns}/Classes/{name}.md)"
    else:
        return f"[{name}](../Classes/{name}.md)"


def property_link(name, *, showshort=False):
    if name.startswith("/"):
        _, other_ns, name = name.split("/")
        showname = name if showshort else f"/{other_ns}/{name}"
        return f"[{showname}](../../{other_ns}/Properties/{name}.md)"
    else:
        return f"[{name}](../Properties/{name}.md)"


def ext_property_link(name):
    (_, pns, pclass, pname) = name.split("/")
    ret = ""
    ret += f"[{pname}](../../{pns}/Properties/{pname}.md)"
    ret += f" from [/{pns}/{pclass}](../../{pns}/Classes/{pclass}.md)"
    return ret


def type_link(name, model, *, showshort=False):
    if name.startswith("/"):
        dirname = "Classes"
        if name in model.vocabularies:
            dirname = "Vocabularies"
        elif name in model.datatypes:
            dirname = "Datatypes"
        _, other_ns, name = name.split("/")
        showname = name if showshort else f"/{other_ns}/{name}"
        return f"[{showname}](../../{other_ns}/{dirname}/{name}.md)"
    elif name[0].isupper():
        dirname = "Classes"
        p = [x for x in model.vocabularies if x.endswith("/" + name)]
        if len(p) > 0:
            dirname = "Vocabularies"
        else:
            p = [x for x in model.datatypes if x.endswith("/" + name)]
            if len(p) > 0:
                dirname = "Datatypes"
        return f"[{name}](../{dirname}/{name}.md)"
    else:
        return f"{name}"

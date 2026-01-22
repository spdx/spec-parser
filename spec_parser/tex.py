# saving the model as LaTeX input

# SPDX-License-Identifier: Apache-2.0

import logging
import subprocess

from jinja2 import Environment, PackageLoader, select_autoescape

logger = logging.getLogger(__name__)

def gen_tex(model, outpath, cfg):
    jinja = Environment(
        loader=PackageLoader("spec_parser", package_path="templates/tex"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    jinja.globals = cfg.all_as_dict
    jinja.globals["not_none"] = lambda x: str(x) if x is not None else ""
    jinja.globals["tex_escape"] = tex_escape
    jinja.globals["markdown_to_tex"] = markdown_to_tex

    p = outpath

    for ns in model.namespaces:
        d = p / ns.name
        d.mkdir()
        f = d / f"{ns.name}.tex"

        template = jinja.get_template("namespace.tex.j2")
        page = template.render(vars(ns))
        f.write_text(page)

    def _generate_in_dir(dirname, group, tmplfname):
        for s in group.values():
            in_ns = s.ns
            d = p / in_ns.name / dirname
            d.mkdir(exist_ok=True)
            f = d / f"{s.name}.tex"

            template = jinja.get_template(tmplfname)
            page = template.render(vars(s))
            f.write_text(page)

    _generate_in_dir("Classes", model.classes, "class.tex.j2")
    _generate_in_dir("Properties", model.properties, "property.tex.j2")
    _generate_in_dir("Vocabularies", model.vocabularies, "vocabulary.tex.j2")
    _generate_in_dir("Individuals", model.individuals, "individual.tex.j2")
    _generate_in_dir("Datatypes", model.datatypes, "datatype.tex.j2")

    def _gen_filelist(nsname, itemslist, heading):
        ret = []
        nameslist = [c.name for c in itemslist.values()]
        if nameslist:
            ret.append(f"\\spdxcategory{{{heading}}}")
            ret.extend(f"\\input{{model/{nsname}/{heading}/{n}}}" for n in sorted(nameslist))
        return ret

    namespaces = [ns.name for ns in model.namespaces]
    files = dict()
    for ns in model.namespaces:
        nsn = ns.name
        files[nsn] = []
        #         files[nsn].append(f"\\section{{{nsn}}}")
        files[nsn].append(f"\\input{{model/{nsn}/{nsn}}}")
        files[nsn].extend(_gen_filelist(nsn, ns.classes, "Classes"))
        files[nsn].extend(_gen_filelist(nsn, ns.properties, "Properties"))
        files[nsn].extend(_gen_filelist(nsn, ns.vocabularies, "Vocabularies"))
        files[nsn].extend(_gen_filelist(nsn, ns.individuals, "Individuals"))
        files[nsn].extend(_gen_filelist(nsn, ns.datatypes, "Datatypes"))

    filelines = []
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
        "Operations",
        "FunctionalSafety",
    ]:
        if nsname in namespaces:
            filelines.extend(files[nsname])
            namespaces.remove(nsname)

    if namespaces:
        logger.warning("The following namespaces were not processed for TeX generation: %s", ", ".join(namespaces))

    fn = p / "model-files.tex"
    fn.write_text("\n".join(filelines))


def tex_escape(s):
    s = s.replace("\\", "\\textbackslash{}")
    s = s.replace("_", "\\_")
    s = s.replace("&", "\\&")
    s = s.replace("#", "\\#")
    s = s.replace("^", "\\^")
    s = s.replace("$", "\\$")
    return s


def markdown_to_tex(s):
    # Call pandoc to convert from Markdown to TeX
    process = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "latex"], input=s.encode("utf-8"), capture_output=True, check=False
    )
    return process.stdout.decode("utf-8")

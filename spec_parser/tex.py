# saving the model as LaTeX input

# SPDX-License-Identifier: Apache-2.0

import logging
import re
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape


def gen_tex(model, outdir, cfg):

    jinja = Environment(
        loader=PackageLoader("spec_parser", package_path="templates/tex"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    jinja.globals = cfg.all_as_dict
    jinja.globals["not_none"] = lambda x: str(x) if x is not None else ""
    jinja.globals["to_tex"] = to_tex
    jinja.globals["markdown_to_tex"] = markdown_to_tex


    op = Path(outdir)
    p = op / "tex"
    p.mkdir()

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
            for n in sorted(nameslist):
                ret.append(f"\\input{{model/{nsname}/{heading}/{n}}}")
        return ret

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
    for nsname in ["Core", "Software", "Security",
               "Licensing", "SimpleLicensing", "ExpandedLicensing", 
               "Dataset", "AI", "Build", "Lite", "Extension"]:
        filelines.extend(files[nsname])

    fn = op / "model-files.tex"
    fn.write_text("\n".join(filelines))


def to_tex(s):
    s = s.replace("\\", "\\textbackslash{}")
    s = s.replace("_", "\\_")
    s = s.replace("&", "\\&")
    s = s.replace("#", "\\#")
    s = s.replace("^", "\\^")
    s = s.replace("$", "\\$")
#    s = s.replace("\\", "\\textbackslash{}")
#    s = s.replace("<", "$<$")
#    s = s.replace(">", "$>$")
#    s = s.replace("{", "\\{")
#    s = s.replace("}", "\\}")
#    s = s.replace("~", "\\textasciitilde{}")
    return s

LINK_REGEXP = re.compile(r"\[([^\]]+)\]\(([^\)]+)\)")
BOLD_REGEXP = re.compile(r"\*\*([^\*]+)\*\*")
ITALIC_REGEXP = re.compile(r"\*([^\*]+)\*")
PREFORMATTED_REGEXP = re.compile(r"\`([^\`]+)\`")
PREFORMATTED_LINES_REGEXP = re.compile(r"\`\`\`([^\`]+)\`\`\`")
def foo(description):
	description = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', description)
	description = re.sub(r'\*(.+?)\*', r'\\textit{\1}', description)
	description = re.sub(r'`(.+?)`', r'\\texttt{\1}', description)
	description = re.sub(r'\[(.*?)\]\((.*?)\)', r'\\href{\2}{\1}', description)

import subprocess

def markdown_to_tex(s):
	# Call pandoc to convert from Markdown to TeX
	process = subprocess.run(
    	['pandoc', '-f', 'markdown', '-t', 'latex'],
    	input=s.encode('utf-8'),
    	stdout=subprocess.PIPE,
    	stderr=subprocess.PIPE
	)
	return process.stdout.decode('utf-8')


# saving the model as RDF

# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape


def gen_mkdocs(model, dir, cfg):
    p = Path(dir)
    if p.exists():
        logging.error(f"Destination for mkdocs {dir} already exists, will not overwrite")
        return
    
    jinja = Environment(
        loader=PackageLoader("spec_parser", package_path="templates/default"),            
        autoescape=select_autoescape(),
        trim_blocks=True, lstrip_blocks=True
    )
    jinja.globals = cfg.all_as_dict

    p.mkdir()

    for ns in model.namespaces:
        d = p / ns.name
        d.mkdir()
        f = d / f"{ns.name}.md"

        template = jinja.get_template("namespace.md.j2")
        page = template.render(vars(ns))
        f.write_text(page)


    def _generate_in_dir(dirname, group, tmplfname):
        for s in group:
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


# saving the model as MkDocs input

# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape


def gen_mkdocs(model, dir, cfg):
    p = Path(dir)
    if p.exists():
        if not cfg.opt_force:
            logging.error(f"Destination for mkdocs {dir} already exists, will not overwrite")
            return
    
    jinja = Environment(
        loader=PackageLoader("spec_parser", package_path="templates/mkdocs"),            
        autoescape=select_autoescape(),
        trim_blocks=True, lstrip_blocks=True
    )
    jinja.globals = cfg.all_as_dict
    jinja.globals["class_link"] = class_link
    jinja.globals["property_link"] = property_link
    jinja.globals["type_link"] = lambda x : type_link(x, model)

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



def class_link(name):
    if name.startswith("/"):
        _, other_ns, name = name.split("/")
        return f"[/{other_ns}/{name}](../../{other_ns}/Classes/{name}.md)"
    else:
        return f"[{name}](../Classes/{name}.md)"    


def property_link(name):
    if name.startswith("/"):
        _, other_ns, name = name.split("/")
        return f"[/{other_ns}/{name}](../../{other_ns}/Properties/{name}.md)"
    else:
        return f"[{name}](../Properties/{name}.md)"


def type_link(name, model):
    if name.startswith("/"):
        name = name[1:]
        dirname = "Classes"
        if name in model.vocabularies:
            dirname = "Vocabularies"
        elif name in model.datatypes:
            dirname = "Datatypes"
        other_ns, name = name.split("/")
        return f"[/{other_ns}/{name}](../../{other_ns}/{dirname}/{name}.md)"
    elif name[0].isupper():
        dirname = "Classes"
        p = [x for x in model.vocabularies if x.endswith('/'+name)]
        if len(p) > 0:
            dirname = "Vocabularies"
        else:
            p = [x for x in model.datatypes if x.endswith('/'+name)]
            if len(p) > 0:
                dirname = "Datatypes"
        return f"[{name}](../{dirname}/{name}.md)"
    else:
        return f"{name}"


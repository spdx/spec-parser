# saving the model as MkDocs input

# SPDX-License-Identifier: Apache-2.0

from jinja2 import Environment, PackageLoader, select_autoescape


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
    jinja.globals["type_link"] = lambda x, showshort=False: type_link(
        x, model, showshort=showshort
    )
    jinja.globals["not_none"] = lambda x: str(x) if x is not None else ""
    jinja.globals["get_subclass_tree"] = lambda x: get_subclass_tree(x, model)
    jinja.globals["get_class_url"] = get_class_url

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

            context = vars(s).copy()

            # For classes, compute direct and nested subclasses
            if dirname == "Classes" and hasattr(s, "subclasses"):
                # Calculate direct subclasses (they are already stored in s.subclasses)

                # Create a map of class to its direct subclasses (as Class objects, not just names)
                direct_subclasses = []
                for subclass_name in s.subclasses:
                    subclass = model.classes.get(subclass_name)
                    if subclass:
                        direct_subclasses.append(subclass)

                context["direct_subclasses"] = direct_subclasses

            template = jinja.get_template(tmplfname)
            page = template.render(context)
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
            ret.extend(
                f"      - '{n}': model/{nsname}/{heading}/{n}.md"
                for n in sorted(nameslist)
            )
        return ret

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
    ]:
        filelines.extend(files[nsname])

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


def get_subclass_tree(class_name, model):
    """Build a nested structure representing the subclass tree for a given class.

    Returns a list of dictionaries, each with 'name' and 'children' keys.
    """
    result = []
    cls = model.classes.get(class_name)

    if not cls or not hasattr(cls, "subclasses") or not cls.subclasses:
        return result

    for subclass_name in cls.subclasses:
        subclass_info = {
            "name": subclass_name,
            "children": get_subclass_tree(subclass_name, model),
        }
        result.append(subclass_info)

    return result


def get_class_url(class_name):
    """Generate a URL for a class based on its fully qualified name.

    Args:
        class_name: Fully qualified class name like "/Namespace/ClassName"

    Returns:
        URL string that works in MkDocs
    """
    parts = class_name.split("/")
    if len(parts) >= 3:
        namespace = parts[1]
        class_name = parts[2]
        # Format for MkDocs
        return f"../../{namespace}/Classes/{class_name}"
    return "#"

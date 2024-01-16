# generate PlantUML input for a diagram

# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

def gen_plantuml(model, dir, cfg):
    p = Path(dir)
    p.mkdir(exist_ok=True)

    f = p / "model.plantuml"

    s = f'''
@startuml
'{cfg.autogen_header}

title SPDXv3 model
scale 4000*4000
hide methods
skinparam packageStyle folder

'''
    for ns in model.namespaces:
        s += f'package {ns.name} {{\n}}\n'

    inheritances = []
    prop2class = []
    for c in model.classes.values():
        if c.metadata["Instantiability"] == "Abstract":
            s += "abstract "
        else:
            s += "class "
        s += f'{c.ns.name}.{c.name} {{\n'
        if "SubclassOf" in c.metadata:
            parent = c.metadata["SubclassOf"]
            inheritances.append((f'{c.ns.name}.{c.name}', parent.split("/")[-1]))
        for p in sorted(c.properties):
            s += f'\t{p} {c.properties[p]["minCount"]}:{c.properties[p]["maxCount"]}\n'
            t = c.properties[p]["type"]
            if ':' not in t:
                prop2class.append((f'{c.ns.name}.{c.name}::{p}', t.split("/")[-1]))
        s += '}\n'

    for v in model.vocabularies.values():
        s += f'enum {v.ns.name}.{v.name} {{\n}}\n'

    for d in model.datatypes.values():
        s += f'class {d.ns.name}.{d.name} {{\n}}\n'


    for pair in inheritances:
        (l,r) = pair
        s += f'{l} <|-- {r}\n'
    for pair in prop2class:
        (l,r) = pair
        s += f'{l} --> {r}\n'

    s += '\n@enduml\n'

    f.write_text(s)

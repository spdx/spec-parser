# saving the model as MkDocs input

# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path

'''
Generates a redirects.json file conforming to the AWS S3 redirect configuration format
'''
def gen_redirects(model, filepath, cfg):
    p = Path(filepath)
    if p.exists():
        if not cfg.opt_force:
            logging.error(f"Destination for redirects JSON file {filepath} already exists, will not overwrite")
            return
    def _generate_redirect_group(file, group_name, group):
        for s in group.values():
            weblocation = f'spdx-spec/v3.0/model/{s.ns.name}/{group_name}/{s.name}/index.html'
            awskey = f'rdf/v3/{s.ns.name}/{s.name}'
            writeredirect(file, awskey, weblocation)
            
    with open(p, 'w+') as f:
        f.write('[\n')
        _generate_redirect_group(f, "Classes", model.classes)
        _generate_redirect_group(f, "Properties", model.properties)
        _generate_redirect_group(f, "Vocabularies", model.vocabularies)
        _generate_redirect_group(f, "Individuals", model.individuals)
        _generate_redirect_group(f, "Datatypes", model.datatypes)
        for ns in model.namespaces:
            weblocation = f'spdx-spec/v3.0/model/{ns.name}/{ns.name}/index.html'
            awskey = f'rdf/v3/{ns.name}'
            writeredirect(f, awskey, weblocation)
        f.write('\n')
        f.write(']\n')

def writeredirect(file, awskey, weblocation):
    if file.tell() > 5:
        file.write(',\n')
    file.write('   {\n')
    file.write('      "Condition": {\n')
    file.write(f'         "KeyPrefixEquals": "{awskey}"\n')
    file.write('      },\n')
    file.write('      "Redirect": {\n')
    file.write('         "HostName": "spdx.github.io",\n')
    file.write(f'         "ReplaceKeyWith": "{weblocation}"\n')
    file.write('      }\n')
    file.write('   }')

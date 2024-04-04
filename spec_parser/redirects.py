# Creates redirects for the model references to the spec website

# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path


def gen_redirects(model, dir, cfg):
    p = Path(dir)
    if p.exists():
        if not cfg.opt_force:
            logging.error(f"Destination for redirects {dir} already exists, will not overwrite")
            return

    p.mkdir()

    for ns in model.namespaces:
        d = p / ns.name
        d.mkdir()
        
        ''' The following does not work since it duplicates the name of the directory
        f = p / ns.name
        
        redirect = f'https://spdx.github.io/spdx-spec/v3.0/model/{ns.name}/{ns.name}/index.html'
        page = gen_html_redirect(redirect)
        f.write_text(page)
        '''

    def _generate_in_dir(dirname, group, tmplfname):
        for s in group.values():
            in_ns = s.ns
            d = p / in_ns.name
            d.mkdir(exist_ok=True)
            f = d / s.name
            redirect = f'https://spdx.github.io/spdx-spec/v3.0/model/{in_ns.name}/{dirname}/{s.name}/index.html'
            page = gen_html_redirect(redirect)
            f.write_text(page)

    _generate_in_dir("Classes", model.classes, "class.md.j2")
    _generate_in_dir("Properties", model.properties, "property.md.j2")
    _generate_in_dir("Vocabularies", model.vocabularies, "vocabulary.md.j2")
    _generate_in_dir("Individuals", model.individuals, "individual.md.j2")
    _generate_in_dir("Datatypes", model.datatypes, "datatype.md.j2")

def gen_html_redirect(redirect):
    retval = '<!DOCTYPE html>\n'
    retval = retval + '<html lang="en">\n'
    retval = retval + '   <head>\n'
    retval = retval + '      <title>SPDX Model</title>\n'
    retval = retval + f'      <meta http-equiv="refresh" content="0; URL={redirect}">\n'
    retval = retval + '   </head>\n'
    retval = retval + '</html>'
    return retval

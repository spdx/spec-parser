# saving the model as JSON

# SPDX-License-Identifier: Apache-2.0

import jsonpickle

def gen_jsondump(model, outpath, cfg):
    f = outpath / "model.json"
    f.write_text(jsonpickle.encode(model, indent=2, warn=True))

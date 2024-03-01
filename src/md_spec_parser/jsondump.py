# saving the model as JSON

# SPDX-License-Identifier: Apache-2.0

import jsonpickle
from pathlib import Path

def gen_jsondump(model, dir, cfg):
    p = Path(dir)
    p.mkdir(exist_ok=True)

    f = p / "model.json"
    f.write_text(jsonpickle.encode(model, indent=2, warn=True))


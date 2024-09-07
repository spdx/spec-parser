# saving the model as JSON

# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path

import jsonpickle


def gen_jsondump(model, outdir, cfg):
    p = Path(outdir) / "jsondump"
    if p.exists() and not cfg.opt_force:
        logging.error(f"Destination for JSON dump: {p} already exists, will not overwrite")
        return
    p.mkdir(exist_ok=True)

    f = p / "model.json"

    f.write_text(jsonpickle.encode(model, indent=2, warn=True))

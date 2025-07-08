# saving the model as JSON

# SPDX-License-Identifier: Apache-2.0

import logging

import jsonpickle

logger = logging.getLogger(__name__)


def gen_jsondump(model, outpath, cfg):
    f = outpath / "model.json"
    f.write_text(jsonpickle.encode(model, indent=2, warn=True))


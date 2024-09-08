# main script called on the command-line

# SPDX-License-Identifier: Apache-2.0

import logging
import warnings

from runparams import RunParams
from spec_parser import Model

if __name__ == "__main__":
    cfg = RunParams()

    if cfg.opt_quiet:
        logging.basicConfig(level=logging.ERROR)
        warnings.filterwarnings("ignore", module="rdflib")
    elif cfg.opt_debug:
        logging.basicConfig(level=logging.DEBUG)
        warnings.filterwarnings("default", module="rdflib")
    elif cfg.opt_verbose:
        logging.basicConfig(level=logging.INFO)
        warnings.filterwarnings("module", module="rdflib")
    else:
        logging.basicConfig(level=logging.WARNING)
        warnings.filterwarnings("once", module="rdflib")
        warnings.filterwarnings("ignore", category=UserWarning)

    m = Model(cfg.input_dir)
    if not cfg.opt_nooutput:
        m.gen_all(cfg.output_dir, cfg)

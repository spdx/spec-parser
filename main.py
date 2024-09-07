# main script called on the command-line

# SPDX-License-Identifier: Apache-2.0

import logging

from runparams import RunParams
from spec_parser import Model

if __name__ == "__main__":
    cfg = RunParams()

    if cfg.opt_quiet:
        logging.basicConfig(level=logging.ERROR)
    elif cfg.opt_debug:
        logging.basicConfig(level=logging.DEBUG)
    elif cfg.opt_verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    m = Model(cfg.input_dir)

    if not cfg.opt_nooutput and cfg.output_dir:
        m.generate(cfg.output_dir, cfg)

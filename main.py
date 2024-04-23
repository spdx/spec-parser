# main script called on the command-line

# SPDX-License-Identifier: Apache-2.0

from runparams import RunParams
from spec_parser import Model

if __name__ == "__main__":
    cfg = RunParams()

    m = Model(cfg.input_dir)
    if not cfg.opt_nooutput:
        m.gen_all(cfg.output_dir, cfg)

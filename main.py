# main script called on the command-line

# SPDX-License-Identifier: Apache-2.0

from spec_parser import Model
from runparams import RunParams

if __name__ == "__main__":
    cfg = RunParams()

    m = Model(cfg.input_dir)
    m.gen_all(cfg.output_dir, cfg)


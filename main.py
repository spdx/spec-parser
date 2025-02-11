# main script called on the command-line

# SPDX-License-Identifier: Apache-2.0

from runparams import RunParams
from spec_parser import Model

if __name__ == "__main__":
    cfg = RunParams("spec-parser")

    m = Model(cfg.input_path)
    if not cfg.no_output:
        m.generate(cfg)

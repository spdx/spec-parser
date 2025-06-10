# main script called on the command-line

# SPDX-License-Identifier: Apache-2.0

from runparams import RunParams
from spec_parser import Model

if __name__ == "__main__":
    cfg = RunParams("spec-parser")

    m = Model(cfg.input_path)
    if not cfg.no_output:
        m.generate(cfg)

    if m.log_handler.num_errors() > 0:
        print(f"Model errors: {m.log_handler.num_errors()}")
        for msg in m.log_handler.error_records:
            print(msg)
        exit(1)

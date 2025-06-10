# main script called on the command-line

# SPDX-License-Identifier: Apache-2.0

import logging

from runparams import LogCountingHandler, RunParams
from spec_parser import Model

if __name__ == "__main__":
    cfg = RunParams("spec-parser")

    m = Model(cfg.input_path)
    if not cfg.no_output:
        m.generate(cfg)

    loggers = [
        ("spec_parser.mdparsing", "Markdown parsing"),
        ("spec_parser.model", "Model"),
        ("spec_parser.rdf", "RDF generation"),
    ]  # Ordered by processing sequence

    total_errors = 0

    for logger_name, label in loggers:
        logger = logging.getLogger(logger_name)
        handler = next((h for h in logger.handlers if isinstance(h, LogCountingHandler)), None)
        if handler and handler.num_errors() > 0:
            num_errors = handler.num_errors()
            print(f"\n{label} errors: {num_errors}")
            for idx, msg in enumerate(sorted(handler.error_records), total_errors + 1):
                print(f"{idx:3}: {msg}")
            total_errors += num_errors

    if total_errors > 0:
        print(f"\nTotal errors: {total_errors}")
        exit(1)

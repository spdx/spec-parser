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

    # Logger names and their labels for error reporting,
    # ordered by processing sequence.
    loggers = [
        ("spec_parser.mdparsing", "Markdown parsing"),
        ("spec_parser.model", "Model"),
        ("spec_parser.rdf", "RDF generation"),
    ]

    total_errors = 0

    for logger_name, label in loggers:
        logger = logging.getLogger(logger_name)
        handler = next(
            (h for h in logger.handlers if isinstance(h, LogCountingHandler)), None
        )  # Get the first LogCountingHandler
        if handler and handler.num_errors() > 0:
            print(f"\n{label} errors: {handler.num_errors()}")
            for idx, msg in enumerate(
                sorted(handler.record[logging.ERROR]), total_errors + 1
            ):
                print(f"{idx:3}: {msg}")
            total_errors += handler.num_errors()

    if total_errors > 0:
        print(f"\nTotal errors: {total_errors}")
        exit(1)

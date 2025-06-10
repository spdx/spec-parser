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

    total_errors = 0
    last_idx = 0

    def report_logger_errors(logger, label, start_idx=1):
        handler = next(
            (h for h in logger.handlers if isinstance(h, LogCountingHandler)), None
        )  # get the LogCountingHandler
        num_errors = 0
        idx = start_idx - 1
        if handler and handler.num_errors() > 0:
            num_errors = handler.num_errors()
            print(f"{label} errors: {num_errors}")
            for idx, msg in enumerate(sorted(handler.error_records), start_idx):
                logger.error(f"{idx:3}: {msg}")
        return num_errors, idx

    errors, last_idx = report_logger_errors(
        logging.getLogger("spec_parser.mdparsing"), "Markdown parsing", last_idx + 1
    )
    total_errors += errors
    print()

    errors, _ = report_logger_errors(
        logging.getLogger("spec_parser.model"), "Model", last_idx + 1
    )
    total_errors += errors
    print()

    if total_errors > 0:
        print(f"Total errors: {total_errors}")
        exit(1)

# main script called on the command-line

# SPDX-License-Identifier: Apache-2.0

import sys

from customlogging import error_printed, setup_logging
from runparams import RunParams
from spec_parser import Model

if __name__ == "__main__":
    root_logger = setup_logging()
    root_logger.info("Spec-parser starts.")

    cfg = RunParams("spec-parser", root_logger)
    if error_printed(root_logger):
        root_logger.error("Errors were logged during the processing of parameters. Exiting.")
        sys.exit(1)

    cfg.create_output_dirs()
    if error_printed(root_logger):
        root_logger.error("Errors were logged during the creation of output directories. Exiting.")
        sys.exit(1)

    m = Model(cfg.input_path)
    if error_printed(root_logger):
        root_logger.error("Errors were logged during the loading of the model. Exiting.")
        sys.exit(1)

    if not cfg.no_output:
        m.generate(cfg)

    if error_printed(root_logger):
        root_logger.error("Errors were logged during the generation of the output. Exiting.")
        sys.exit(1)

# the parameters of a run

# SPDX-License-Identifier: Apache-2.0

import argparse
from datetime import datetime, timezone
import logging
import sys


class RunParams:
    def __init__(self):
        self._ts = datetime.now(timezone.utc)
        self.process_args()

    @property
    def autogen_header(self):
        return f"Automatically generated by spec-parser v{self.parser_version} on {self._ts.isoformat()}"

    @property
    def input_dir(self):
        return self.args.input_dir

    @property
    def output_dir(self):
        return self.args.output_dir

    @property
    def opt_debug(self):
        return self.args.debug

    @property
    def opt_force(self):
        return self.args.force

    @property
    def opt_nooutput(self):
        return self.args.nooutput

    @property
    def opt_quiet(self):
        return self.args.quiet

    @property
    def opt_verbose(self):
        return self.args.verbose

    @property
    def parser_version(self):
        return sys.modules["spec_parser"].__version__

    @property
    def all_as_dict(self):
        return {
            k: getattr(self, k)
            for k in (
                "autogen_header",
                "input_dir",
                "output_dir",
                "opt_debug",
                "opt_force",
                "opt_quiet",
                "opt_verbose",
                "parser_version",
            )
        }

    # TODO: add more parameters, specified as command-line arguments
    # - separate output dirs for mkdocs / RDF /JSON-LD / ...
    # - maybe flags whether something might not be generated?
    # - etc.

    def process_args(self, args=sys.argv[1:]):
        parser = argparse.ArgumentParser(description="Generate documentation from an SPDX 3.0 model")
        parser.add_argument("input_dir", help="Directory containing the input specification files")
        parser.add_argument("output_dir", nargs="?", help="Directory to write the output files to")
        parser.add_argument("-d", "--debug", action="store_true", help="Print debug output")
        parser.add_argument("-f", "--force", action="store_true", help="Overwrite existing generated files")
        parser.add_argument("-n", "--nooutput", action="store_true", help="Do not generate anything, only check input")
        parser.add_argument("-q", "--quiet", action="store_true", help="Print no output")
        parser.add_argument("-v", "--verbose", action="store_true", help="Print verbose output")
        parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {RunParams.parser_version}")
        self.args = parser.parse_args(args)

        if self.opt_nooutput:
            if self.output_dir:
                logging.warning(f"Ignoring output directory {self.output_dir} specified with --nooutput")
        else:
            if not self.output_dir:
                logging.critical(f"No output directory specified!")

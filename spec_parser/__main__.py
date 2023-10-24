import logging
import os
from argparse import ArgumentParser

from spec_parser import SpecParser, isError


def get_args():
    argparser = ArgumentParser(
        prog="spec-parser", description="SPDX specification parser"
    )

    argparser.add_argument("spec_dir", type=str, help="Directory containing specs")

    argparser.add_argument("--gen-md", action="store_true", help="Dumps markdown")

    argparser.add_argument(
        "--gen-refs", action="store_true", help="Generate References list for Property"
    )

    argparser.add_argument(
        "--json-dump",
        action="store_true",
        help="Dump the JSON representation of the markdown files.",
    )

    argparser.add_argument(
        "--gen-rdf",
        action="store_true",
        help="Experimental! Generate RDF in turtle format",
    )

    argparser.add_argument(
        "--use-table",
        action="store_true",
        help="Use markdown-table to display properties in `Class` entity",
    )

    argparser.add_argument(
        "--out-dir",
        type=str,
        default="md_generated",
        help="Output Directory for generating markdown",
    )

    args = argparser.parse_args()

    return args

def main():
    args = get_args()

    if not os.path.isdir(args.spec_dir):
        logging.error(
            f"Error: Directory containing models :{args.spec_dir} doesn't exists"
        )
        exit(1)

    specParser = SpecParser(**vars(args))
    spec = specParser.parse(args.spec_dir)
    if isError():
        logging.error(f"Spec not parsed successfully.")
        exit(1)
    if args.json_dump:
        spec.gen_json_dump()
    if args.gen_md:
        spec.gen_md()
    if args.gen_rdf:
        spec.gen_rdf()

if __name__ == "__main__":
    main()

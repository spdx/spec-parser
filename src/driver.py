import os
from argparse import ArgumentParser
from spec_parser import SpecParser


def get_args():

    argparser = ArgumentParser(prog='spec-parser',
                               description='SPDX specification parser')

    argparser.add_argument('spec_dir', type=str,
                           help='Directory containing specs')

    argparser.add_argument('--md', action="store_true",
                           help='Dumps markdown')

    argparser.add_argument('--out', type=str,
                           help='Output Directory for generating markdown')

    args = argparser.parse_args(["--md", "spec-v3-template/model"])

    return args


if __name__ == '__main__':

    args = get_args()

    if not os.path.isdir(args.spec_dir):
        print(
            f'ERROR: Directory containing models :{args.spec_dir} doesn\'t exists')
        exit(1)

    if args.out is None:
        args.out = 'md_generated'

    specParser = SpecParser()
    spec = specParser.parse(args.spec_dir)

    if args.md:
        spec.dump_md(args.out)

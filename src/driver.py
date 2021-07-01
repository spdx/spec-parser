import os
from argparse import ArgumentParser
from spec_parser import SpecParser


def get_args():

    argparser = ArgumentParser(prog='spec-parser',
                               description='SPDX specification parser')

    argparser.add_argument('model', type=str,
                           help='Directory containing Models')

    argparser.add_argument('profile', type=str,
                           help='Directory containing Profiles')

    argparser.add_argument('--md', action="store_true",
                           help='Dumps markdown')

    argparser.add_argument('--out', type=str,
                           help='Output Directory for generating markdown')

    args = argparser.parse_args()

    return args


if __name__ == '__main__':

    args = get_args()

    if not os.path.isdir(args.model):
        print(
            f'ERROR: Directory containing models :{args.model} doesn\'t exists')
        exit(1)

    if not os.path.isdir(args.profile):
        print(
            f'ERROR: Directory containing profiles :{args.profile} doesn\'t exists')
        exit(1)

    if args.out is None:
        args.out = 'md_generated'

    specParser = SpecParser()
    spec = specParser.parse(args.model, args.profile, args.md, args.out)

    if args.md:
        spec.dump_md(args.out)

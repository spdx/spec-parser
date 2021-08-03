import os
import logging
from argparse import ArgumentParser
from helper import ErrorFoundFilter


def get_args():

    argparser = ArgumentParser(prog='spec-parser',
                               description='SPDX specification parser')

    argparser.add_argument('spec_dir', type=str,
                           help='Directory containing specs')

    argparser.add_argument('--md', action="store_true",
                           help='Dumps markdown')

    argparser.add_argument('--refs', action="store_true",
                           help='Generate References list for Property')

    argparser.add_argument('--out', type=str,
                           help='Output Directory for generating markdown')

    args = argparser.parse_args()

    return args


if __name__ == '__main__':

    args = get_args()

    logging.basicConfig(format='%(name)-18s: %(levelname)-8s %(message)s')
    logger = logging.getLogger()
    for handler in logger.handlers:
        handler.addFilter(ErrorFoundFilter())
        break

    if not os.path.isdir(args.spec_dir):
        logger.error(
            f'Error: Directory containing models :{args.spec_dir} doesn\'t exists')
        exit(1)

    if args.out is None:
        args.out = 'md_generated'

    from spec_parser import SpecParser
    specParser = SpecParser()
    spec = specParser.parse(args.spec_dir)
    if args.md:
        spec.dump_md(args)

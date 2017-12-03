import argparse
import fileinput
import logging
import os
import shutil
import sys
from sf2heat import Sf2heat

DESCRIPTION = '''Sf2heat CLI takes a set of Superfluity descriptors as an input(YAML or JSON), calls an appropriate parser, 
maps it to Heat resources and then produces a Heat Orchestration Template (HOT) as an output.
This requires that you have Python 2.7.
'''

SUPPORTED_FILE = ['json', 'JSON', 'yaml', 'YAML']
SUPPORTED_TYPES = ['superfluidity', 'SUPERFLUIDITY']


def init_logger(logger_name):
    logger = logging.getLogger(logger_name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)s] '
                                      '[%(name)s] %(message)s',
                                  datefmt='%H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter, prog='SF2HEAT CLI')
    verb_group = parser.add_mutually_exclusive_group()
    verb_group.add_argument('-v', '--verbose', action='store_true',
                               help='Verbose level logging to shell.')
    verb_group.add_argument('-q', '--quiet', action='store_true',
                               help='Only print errors.')

    parser.add_argument('--files-extension',
                        metavar='<input-file-extension>',
                        choices=SUPPORTED_FILE,
                        default='json',
                        help=(('File extension to parse. Choose between '
                                '%s.') % SUPPORTED_FILE))
    parser.add_argument('--descriptors-type',
                        metavar='<input-file-extension>',
                        choices=SUPPORTED_TYPES,
                        default='superfluidity',
                        help=(('File extension to parse. Choose between '
                                '%s.') % SUPPORTED_TYPES))
    parser.add_argument('-i', '--input-file',
                        metavar='<input-file>',
                        required=True,
                        choices=Choices('.yaml', '.json'),
                        type=argparse.FileType('r'),
                        help='the file where the HOT should be written')
    parser.add_argument('-o', '--output-file',
                        default=sys.stdout,
                        choices=Choices('.yaml'),
                        help='the file where the HOT should be written')
    parser.add_argument('-d', '--output-directory',
                        #type=readable_dir,
                        help='the directory where the Ansible playbook with HOT should be written')
    parser.add_argument('-a', '--ansible-init',
                        action='store_true',
                        help='Generate the HOT template with an Ansible playbook Cloud init')
    parser.add_argument('--parameters',
                        metavar='<param1=val1;param2=val2;...>',
                        help='Optional input parameters.')

    return parser.parse_args(args)

lgr = init_logger(__file__)


class Choices():
    def __init__(self, *choices):
        self.choices = choices

    def __contains__(self, choice):
        # True if choice ends with one of self.choices

        choice = choice.name if isinstance(choice, file) else choice
        return any(choice.endswith(c) for c in self.choices)

    def __iter__(self):
        return iter(self.choices)

if __name__ == '__main__':
    args = parse_args()
    if args.quiet:
        lgr.setLevel(logging.ERROR)
    elif args.verbose:
        lgr.setLevel(logging.DEBUG)
    else:
        lgr.setLevel(logging.INFO)

    xargs = ['quiet', 'verbose', 'files_extension']
    args = {arg: v for arg, v in vars(args).items() if arg not in xargs}
    sf2heat = Sf2heat(**args)
    sf2heat.translate()

# -*- encoding: utf8 -*-

# region LICENSE
# ------------------------------------------------------------------------------
# The MIT License
#
#
# Copyright 2023 Jorge A. Gomes
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ------------------------------------------------------------------------------
# endregion (license)

# region IMPORTS

import sys

from typing import Any, Sequence
from argparse import ArgumentParser, Namespace, FileType
from io import TextIOWrapper
from colorama import just_fix_windows_console

from core.parser import *


# endregion (imports)
# ---------------------------------------------------------
# region EXPORTS


__all__ = [
    '',
]


# endregion (exports)
# ---------------------------------------------------------
# region CONSTANTS & ENUMS

VERBOSITY_MAP = {
    'error': ERROR,
    'warning': WARNING,
    'debug1': DEBUG1,
    'success': SUCCESS,
    'debug2': DEBUG2,
    'info': INFO,
    'debug3': DEBUG3,
    'all': ALL,
}

# endregion (constants)
# ---------------------------------------------------------
# region CLASSES

# endregion (classes)
# ---------------------------------------------------------
# region FUNCTIONS


def main() -> int:

    just_fix_windows_console()

    parser = ArgumentParser()
    parser.add_argument('grammar', help="The language grammar file path", type=FileType('r', encoding='utf8'))
    parser.add_argument('-o', '--out', help="The language parser output file path", type=FileType('w', encoding='utf8'), required=True)
    parser.add_argument('-v', '--verbosity', help="Set the verbosity level", choices=['error', 'warning', 'debug1', 'success', 'debug2', 'info', 'debug3', 'all'], default='debug1')

    args: Namespace = parser.parse_args()

    contents = args.grammar.read()
    nodes: GrammarNodes = parse(contents, args.grammar.name, args.out.name, verbosity=VERBOSITY_MAP.get(args.verbosity, ERROR))
    # sparser = gparser.generate_parser(contents, args.grammar.name)

    # args.out.write(sparser)

    return 0


# endregion (functions)
# ---------------------------------------------------------
# region ENTRYPOINT


if __name__ == '__main__':
    sys.exit(main())

# endregion (entrypoint)

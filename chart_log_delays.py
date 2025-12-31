#!/usr/bin/env python3

import os
import sys
from argparse import ArgumentParser
from typing import Callable
from pathlib import Path
import traceback

__author__ = "David Blume"
__copyright__ = "Copyright 2016-2022, David Blume"
__license__ = "MIT"
__version__ = "1.0"
__status__ = "Development"


def filenum_excepthook(exc_type, exc_value, tb):
    """Print errors as:
         File path/file.py:##
       not:
         File path/file.py, line ##"""
    for line in traceback.format_exception(exc_type, exc_value, tb):
        if line.startswith('  File'):
            print(line.replace(', line ', ':'), end='', file=sys.stderr)
        else:
            print(line, end='', file=sys.stderr)

sys.excepthook = filenum_excepthook

# This class demonstrates decorators.
#
# Consider these alternatives for data classes:
# * dataclasses.dataclass: sensible defaults, compares class type, can be frozen
#                          See "bored" module for data validation with marshmallow
# * collections.namedtuple: esp. useful for results of csv and sqlite3
class Coffee:

    def __init__(self, price: float):
        super().__init__()  # See https://eugeneyan.com/writing/uncommon-python/
        self._price = price

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, new_price: float) -> None:
        if new_price > 0 and isinstance(new_price, float):
            self._price = new_price
        else:
            raise ValueError("price must be a non-negative float.")


def main(debug: bool) -> None:
    script_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
    print(f'{sys.argv[0]} is in {script_dir}.')


    if debug and (Path.home() / 'bin').exists():
        print('Your home directory has a bin/ directory.')

    cuppa = Coffee(5.00)
    cuppa.price = cuppa.price - 1.00
    print(f'Coffee on sale for ${cuppa.price:1.2f}.')


if __name__ == '__main__':
    parser = ArgumentParser(description='Just a template sample.')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    main(args.debug)

#!/usr/bin/env python3
# git ls-files | entr -c sh -c 'ctags -R *; ./chart_log_delays.py'

import os
import sys
from argparse import ArgumentParser
from typing import Callable
from pathlib import Path
from collections import namedtuple
import datetime
import traceback

__author__ = "David Blume"
__copyright__ = "Copyright 2025, David Blume"
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

Log = namedtuple('Log', ['first_occur', 'frequency_s', 'filename', 'url'])

Logs = [#Log('2024-12-22, 20:30',            -1,      'fm_stats.txt',     'https://david.dlma.com/location/fm_stats.txt'),
        #Log('Sat Dec 20 12:30:00 PST 2025', 60 * 60, 'dreamhost_30.txt', 'https://dblu.me/dreamhost_30.txt'),
        Log('Sat Dec 20 12:00:00 PST 2025', 60 * 60, 'dreamhost_00.txt', 'https://dblu.me/dreamhost_00.txt'),
        #Log('Thu Dec 18 11:00:00 PST 2025', 30 * 60, 'dreamhost.txt',    'https://dblu.me/dreamhost.txt'),
       ]

# We'll have to be clever about processing fm_stats.txt because it has various offsets.
# 9:30, 20:30: https://david.dlma.com/location/fm_stats.txt

def main(debug: bool) -> None:
    script_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
    #print(f'{sys.argv[0]} is in {script_dir}.')

    for log in Logs:
        expected = datetime.datetime.strptime(log.first_occur, '%a %b %d %H:%M:%S %Z %Y')
        print(f'{log.filename} updates every {log.frequency_s} seconds, first at {log.first_occur}, {expected=}')
        with open(log.filename, 'r', encoding='utf-8') as f:
            i = 0
            for line in f:
                i += 1
                observed = datetime.datetime.strptime(line[:28], '%a %b %d %H:%M:%S %Z %Y')
                print(f"{observed} - {expected} = {observed - expected}")
                expected = expected + datetime.timedelta(seconds=log.frequency_s)
                if i >= 10:
                    break


if __name__ == '__main__':
    parser = ArgumentParser(description='Just a template sample.')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    main(args.debug)

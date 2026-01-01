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
import subprocess

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

Log = namedtuple('Log', ['hour_offset', 'frequency_s', 'filename', 'url'])

Logs = [Log(30, -1,      'fm_stats.txt',     'https://david.dlma.com/location/fm_stats.txt'),
        #Log(30, 60 * 60, 'dreamhost_30.txt', 'https://dblu.me/dreamhost_30.txt'),
        Log(00, 60 * 60, 'dreamhost_00.txt', 'https://dblu.me/dreamhost_00.txt'),
        #Log(00, 30 * 60, 'dreamhost.txt',    'https://dblu.me/dreamhost.txt'),
       ]

CRON_TIMEOUT = 60 * 60  # 1 hour


def next_expected(prev_expected: datetime.datetime, frequency_s: int) -> datetime.datetime:
    if frequency_s > 0:
        return prev_expected + datetime.timedelta(seconds=frequency_s)
    else:
        # Custom schedule for fm_stats.txt, which runs at 09:30 and 20:30
        if prev_expected.hour < 20:
            return prev_expected + datetime.timedelta(hours=11)
        else:
            return prev_expected + datetime.timedelta(hours=13)


def main(debug: bool) -> None:
    script_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
    #print(f'{sys.argv[0]} is in {script_dir}.')

    for log in Logs:
        print(f'{log.filename} updates every {log.frequency_s}')
        with open(log.filename, 'r', encoding='utf-8') as f:
            i = 0
            scheduled_runs = list()
            if log.frequency_s > 0:
                max_duration_s = min(log.frequency_s, CRON_TIMEOUT)
            else:
                max_duration_s = CRON_TIMEOUT
            for line in f:
                if line[0].isdigit():
                    observed = datetime.datetime.strptime(line[:17], '%Y-%m-%d, %H:%M')
                else:
                    observed = datetime.datetime.strptime(line[:28], '%a %b %d %H:%M:%S %Z %Y')
                if i == 0:
                    expected = observed.replace(minute=log.hour_offset, second=0)

                # if a cronjob doesn't run within an hour, it gets abandoned.
                # So this observed may be several expected runs later.
                while (observed - expected).total_seconds() > max_duration_s:
                    scheduled_runs.append((expected, max_duration_s))
                    expected = next_expected(expected, log.frequency_s)
                scheduled_runs.append((expected, max(0, (observed - expected).total_seconds())))
                expected = next_expected(expected, log.frequency_s)
                i += 1

        for i in scheduled_runs:
            if i[1] < 0:
                print(f"{i[0].strftime('%Y-%m-%d %H:%M')} {int(i[1])} {log.filename}")

        with subprocess.Popen(["gnuplot"], stdin=subprocess.PIPE, encoding='utf8') as gnuplot:
            plot_to_png = True
            if plot_to_png:
                gnuplot.stdin.write(f"set term png size 1600,500; set output '{log.filename}.png'\n")
            else:
                gnuplot.stdin.write("set term block braille size `tput cols`,`tput lines`*4/9\n")
            clean_filename = log.filename.replace('_', '-')
            gnuplot.stdin.write(f'set label "{clean_filename}" at graph 0.03, 0.9\n')
            gnuplot.stdin.write(f"set xdata time\n")
            gnuplot.stdin.write(f"set timefmt \"%Y-%m-%dT%H-%M\"\n")
            gnuplot.stdin.write("set xtics rotate by -45\n")
            #gnuplot.stdin.write(f"set xrange [{rmin}:{rmax}]\n")
            #gnuplot.stdin.write("set yrange [0:100]\n")
            gnuplot.stdin.write(f"set style fill solid 0.5\n")
            gnuplot.stdin.write(f"set key opaque\n")
            #gnuplot.stdin.write(f"plot '-' using 1:2 title 'cronjob delays in minutes' at 0.19, 0.84 with boxes\n")
            gnuplot.stdin.write(f"plot '-' using 1:2 title 'cronjob delays in minutes' with boxes\n")
            for i in scheduled_runs:
               gnuplot.stdin.write(f"{i[0].strftime('%Y-%m-%dT%H-%M')} {int(i[1]/60)}\n")
            gnuplot.stdin.write("e\n")
            gnuplot.stdin.flush()

if __name__ == '__main__':
    parser = ArgumentParser(description='Just a template sample.')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    main(args.debug)

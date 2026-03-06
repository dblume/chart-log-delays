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
import requests

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
        Log(30, 60 * 60, 'dreamhost_30.txt', 'https://dblu.me/dreamhost_30.txt'),
        Log(00, 60 * 60, 'dreamhost_00.txt', 'https://dblu.me/dreamhost_00.txt'),
        #Log(00, 30 * 60, 'dreamhost.txt',    'https://dblu.me/dreamhost.txt'), # <-- half hour cadence, but 1h timeouts cause ambiguity about which run is which.
       ]

CRON_TIMEOUT_S = 60 * 60  # 1 hour


def next_expected(prev_expected: datetime.datetime, frequency_s: int) -> datetime.datetime:
    if frequency_s > 0:
        return prev_expected + datetime.timedelta(seconds=frequency_s)
    else:
        # Custom schedule for fm_stats.txt, which runs at 09:30 and 20:30
        if prev_expected.hour < 20:
            return prev_expected + datetime.timedelta(hours=11)
        else:
            return prev_expected + datetime.timedelta(hours=13)


def CheckCachedLogfile(log: Log) -> None:
    # Download the log file if it doesn't exist or is more than 1 hour old.
    log_path = Path(log.filename)
    if not log_path.exists() or (datetime.datetime.now() - datetime.datetime.fromtimestamp(log_path.stat().st_mtime)).total_seconds() > 60 * 60:
        print(f"Downloading {log.url} to {log.filename}...")
        response = requests.get(log.url)
        response.raise_for_status()
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(response.text)


def PlotLogs(log: Log, days: int, output_format: str = 'png') -> None:
    with open(log.filename, 'r', encoding='utf-8') as f:
        i = 0
        scheduled_runs = list()
        if log.frequency_s > 0:
            max_duration_s = min(log.frequency_s, CRON_TIMEOUT_S)
        else:
            max_duration_s = CRON_TIMEOUT_S
        for line in f:
            # We support three timestamp formats:
            # "2024-06-01, 09:30"
            # "2024-06-01 09:30:33 PST"
            # "Sat Jun 01 09:30:00 UTC 2024"
            if line[0].isdigit():
                if line[10] == ',':
                    observed = datetime.datetime.strptime(line[:17], '%Y-%m-%d, %H:%M')
                else:
                    observed = datetime.datetime.strptime(line[:23], '%Y-%m-%d %H:%M:%S %Z')
            else:
                observed = datetime.datetime.strptime(line[:28], '%a %b %d %H:%M:%S %Z %Y')
            if i == 0:
                # Set a sensible "expected" time for the first observed run.
                expected = observed.replace(minute=log.hour_offset, second=0)
                rmin = expected

            # if a cronjob doesn't run within an hour, it gets abandoned.
            # So this "observed" may actually be several expected runs later.
            while (observed - expected).total_seconds() > max_duration_s:
                scheduled_runs.append((expected, max_duration_s))
                expected = next_expected(expected, log.frequency_s)
            scheduled_runs.append((expected, max(0, (observed - expected).total_seconds())))
            rmax = expected
            expected = next_expected(expected, log.frequency_s)
            i += 1

    if days > 0:
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        scheduled_runs = [r for r in scheduled_runs if r[0] >= cutoff]
        if scheduled_runs:
            rmin = scheduled_runs[0][0]

    if output_format == 'html':
        # Generate HTML with Chart.js
        labels = []
        data = []
        for timestamp, delay_s in scheduled_runs:
            labels.append(timestamp.strftime('%Y-%m-%d %H:%M'))
            data.append(int(delay_s / 60))

        labels_json = str(labels).replace("'", '"')
        data_json = str(data)
        chart_title = log.url.replace("_", "-")

        html_content = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <title>Chart from chart-log-delays</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  </head>
  <body>
    <canvas id="c"></canvas>
    <script>
      new Chart('c', {type:'bar',
                      data:{labels:""" + labels_json + """,
                            datasets:[{barPercentage:1.0,categoryPercentage:1.0,label:'cronjob delays in minutes',data:""" + data_json + """,backgroundColor:'rgb(0, 0, 255, 0.5)'}]},
                      options:{responsive:true,
                               maintainAspectRatio:true,
                               scales:{y:{beginAtZero:true,title:{display:true,text:'cronjob delay (m)'}},
                                       x:{ticks:{autoSkip:false,callback:function(value,index){
                                           const l = this.getLabelForValue(value);
                                           if (index > 0) {
                                               const previousLabel = this.chart.data.labels[index - 1];
                                               return l[8] !== this.chart.data.labels[index - 1][8] || l[9] !== this.chart.data.labels[index - 1][9] ? l.substring(0,10) : '';}
                                           return l.substring(0,10); }}}},
                               plugins:{title:{display:true,text:'""" + chart_title + """'}}}});
    </script>
  </body>
</html>"""

        output_file = f"{log.filename}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Writing {output_file}")
    else:
        # Use gnuplot for PNG and text output
        with subprocess.Popen(["gnuplot"], stdin=subprocess.PIPE, encoding='utf8') as gnuplot:
            if output_format == 'png':
                gnuplot.stdin.write(f"set term png size 1200,400; set output '{log.filename}.png'\n")
                print(f"Writing {log.filename}.png")
            else:  # text
                gnuplot.stdin.write("set term block braille size `tput cols`,`tput lines`*3/9\n")
            clean_filename = log.url.replace('_', '-')
            gnuplot.stdin.write('set style textbox opaque fillcolor "0x20FFFFFF" noborder\n')
            gnuplot.stdin.write(f'set label "{clean_filename}" at graph 0.03, 0.96 boxed front\n')
            gnuplot.stdin.write("set xdata time\n")
            gnuplot.stdin.write(f"set timefmt \"%Y-%m-%dT%H-%M\"\n")

            gnuplot.stdin.write("set xtics 60 * 60 * 24 out rotate by -65\n")
            gnuplot.stdin.write("set format x \"%m-%d-%y\"\n")
            gnuplot.stdin.write('set ylabel "cronjob delay (m)"\n')
            gnuplot.stdin.write(f'set xrange ["{rmin.strftime('%Y-%m-%dT%H-%M')}":"{rmax.strftime('%Y-%m-%dT%H-%M')}"]\n')
            gnuplot.stdin.write(f"set style fill solid 0.5\n")

            if output_format == 'png':
                gnuplot.stdin.write(f'set key opaque fillcolor "0x20FFFFFF"\n')
            gnuplot.stdin.write(f"plot '-' using 1:2 title 'cronjob delays in minutes' with boxes fc 'blue'\n")
            for i in scheduled_runs:
               gnuplot.stdin.write(f"{i[0].strftime('%Y-%m-%dT%H-%M')} {int(i[1]/60)}\n")
            gnuplot.stdin.write("e\n")
            gnuplot.stdin.flush()


def main(days: int, output_format: str) -> None:
    for log in Logs:
        CheckCachedLogfile(log)
        PlotLogs(log, days, output_format)


if __name__ == '__main__':
    parser = ArgumentParser(description='Visualize cronjob delays from log files.')
    parser.add_argument('-d', '--days', type=int, default=0, help='Number of days back to plot')
    parser.add_argument('--out', choices=['png', 'html', 'text'], default='png', help='Output format: png (default), html (Chart.js), or text (braille)')
    args = parser.parse_args()
    main(args.days, args.out)

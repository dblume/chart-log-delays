[![License](https://img.shields.io/badge/license-MIT_license-blue.svg)](https://raw.githubusercontent.com/dblume/chart-log-delays/main/LICENSE)
![python3.x](https://img.shields.io/badge/python-3.x-green.svg)

## Chart Log Delays

This project provides a Python script to analyze and visualize log delays in a chart format. It reads log data, calculates delays, and generates a visual representation of the delays over time.

## Why?

Suppose you have a cronjob run every hour, and it just appends 
the time it ran to a logfile.

    30   *   *   *   *   echo "$(date)" >>cronjob_log.txt

After a few hours, you should *expect* to see a log file with entries like this:

    Sat Feb 14 14:30:00 PST 2026
    Sat Feb 14 15:30:00 PST 2026
    Sat Feb 14 16:30:00 PST 2026
    Sat Feb 14 17:30:00 PST 2026
    Sat Feb 14 18:30:00 PST 2026

But if what you actually see is something like the following? It's a mess.

    Sat Feb 14 14:34:16 PST 2026
    Sat Feb 14 17:33:21 PST 2026
    Sat Feb 14 18:38:59 PST 2026
    Sat Feb 14 23:35:02 PST 2026
    Sun Feb 15 02:33:45 PST 2026

A graph of the delays will reveal just how bad the problem is. Run the script to
analyze the log file and generate a chart of the delays. 

    $ python3 chart_log_delays.py --out png -d 5
![bar chart](https://dblume.github.io/images/chart-log-events_dreamhost_30.png)

Yikes, those tall blue bars are scheduled jobs that never ran. Ideally, you don't
want to see any blue bars at all. Generally, the shorter the better.

There are three output modes you can set with `--out`:

- `png` (default) to save the chart as a PNG image file
- `text` for a simple chart in the terminal (uses braille, so may not render well in all terminals)
- `html` to generate an HTML file with an interactive chart (requires a web browser to view)

During development, use `entr` in another window for continuous testing:

    git ls-files | entr -c sh -c './chart_log_delays.py --cli -d 7'

## Is it any good?

[Yes](https://news.ycombinator.com/item?id=3067434).

## License

This software uses the [MIT license](https://raw.githubusercontent.com/dblume/chart-log-delays/main/LICENSE)

[![License](https://img.shields.io/badge/license-MIT_license-blue.svg)](https://raw.githubusercontent.com/dblume/chart-log-delays/main/LICENSE)
![python3.x](https://img.shields.io/badge/python-3.x-green.svg)
![no AI](https://img.shields.io/badge/AI-none-blue.svg)

## Chart Log Delays

This project provides a Python script to analyze and visualize log delays in a chart format. It reads log data, calculates delays, and generates a visual representation of the delays over time.

### What Happens?

First, have a cronjob run every hour, and just append the time it ran to a logfile.

    30      *       *       *       *     echo "$(date)" >>cronjob_log.txt

Then, run the script to analyze the log file and generate a chart of the delays. Ideally there won't be many delays, but if there are, the chart will show them clearly.

    python3 chart_log_delays.py

During development, use `entr` in another window for continuous testing:

    git ls-files | entr -c sh -c './chart_log_delays.py --cli -d 7'

## Is it any good?

[Yes](https://news.ycombinator.com/item?id=3067434).

## License

This software uses the [MIT license](https://raw.githubusercontent.com/dblume/chart-log-delays/main/LICENSE)

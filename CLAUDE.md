# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`chart_log_delays` is a Python utility that analyzes cronjob execution logs and generates visualizations showing delays in scheduled task execution. It downloads remote log files, parses timestamps, calculates execution delays against expected schedules, and creates PNG charts using gnuplot.

## Running the Project

### Basic usage
```bash
./chart_log_delays.py              # Chart all available data
./chart_log_delays.py -d 7         # Chart data from last 7 days
./chart_log_delays.py --help       # Show available options
```

### Dependencies
- Python 3.x
- gnuplot (for rendering charts)
- requests library (for downloading log files)

Install requests if needed:
```bash
pip install requests
```

## Architecture

### Main Components

**chart_log_delays.py:35-41** - `Logs` configuration
- Defines which remote log files to download and analyze
- Each log entry specifies: hour offset (minute of the hour to expect the run), frequency in seconds, local filename, and remote URL
- Currently tracking `dreamhost_00.txt` (runs hourly at minute 00)
- Other logs are commented out (fm_stats.txt, dreamhost_30.txt)

**chart_log_delays.py:57-65** - `CheckCachedLogfile()`
- Downloads remote log files if they don't exist locally or are older than 1 hour
- Stores files locally for processing

**chart_log_delays.py:68-127** - `PlotLogs()`
- Core logic that:
  1. Parses log files (supports two timestamp formats: `YYYY-MM-DD, HH:MM` and standard Unix log format)
  2. Calculates expected vs observed execution times
  3. Detects missed cron runs (when gap > max_duration_s, assumes run was skipped)
  4. Pipes data to gnuplot for visualization
  5. Outputs PNG charts with delay data in minutes

**chart_log_delays.py:46-55** - `next_expected()`
- Helper function that calculates the next expected execution time
- Handles both regular frequency-based schedules and custom schedules (e.g., fm_stats runs at 09:30 and 20:30)

### Data Processing Flow

1. User runs script with optional `-d/--days` parameter to filter data to the last N days, or `--cli` to display in terminal
2. For each configured log in `Logs`:
   - Download/cache the remote log file
   - Parse timestamps from log file
   - Calculate delay for each cronjob run
   - Handle missed runs (gaps > CRON_TIMEOUT_S)
   - Pipe visualization data to gnuplot
   - Generate PNG chart file

### Timestamp Formats

The parser supports two formats:
- ISO-like: `2024-06-01, 09:30`
- Unix log: `Sat Jun 01 09:30:00 UTC 2024`

### Configuration Constants

- `CRON_TIMEOUT_S` (60 * 60): Maximum expected duration for a cronjob. If a run takes longer or is missed, it's considered abandoned and a new expected run is calculated.

## Development Notes

- The custom exception hook (`filenum_excepthook`) formats error output to match the pattern `file.py:##` instead of standard Python traceback format
- Charts default to PNG output (lines 104-106), but can be rendered to terminal using the `--cli` flag for braille block display (lines 108, 138-140)
- The `-d/--days` parameter filtering is implemented in lines 97-101

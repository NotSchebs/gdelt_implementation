# GDELT Trend Analysis Tool

A small desktop GUI for exploring GDELT keyword trends and optional article metadata.
The app uses `gdeltdoc` to fetch timeline volume data, and it can also retrieve up to 250 articles for the selected date range.

## Features

- Search GDELT timeline data for any keyword over predefined or custom date ranges
- Optionally fetch related articles for the same date range
- Normalize article date metadata so it can be linked to timeline counts
- Export results as:
  - a timeline CSV with daily `n_articles`
  - a ZIP archive containing timeline CSV plus raw article CSV
- Stop button cancels the current fetch and resets the UI
- Built-in retry and rate-limit handling for a smoother user experience

## Requirements

- Python 3.10+ (the project currently runs in a virtual environment)
- `gdeltdoc`
- `pandas`
- `matplotlib`
- `tkinter` (usually included with Python on macOS/Linux)

## Setup

1. Create and activate a virtual environment from the project root:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the app

From the repository root:

```bash
source venv/bin/activate
python3 gdelt_gui_test.py
```

## How it works

- The app fetches timeline volume data with the GDELT `timelinevol` API.
- If `Fetch Articles` is enabled, it will also call `gd.article_search(...)` with `num_records=250`.
- When article results include a date field such as `seendate`, the app converts it to a proper datetime and creates `article_date`.
- The timeline output includes a new `n_articles` column, which counts how many articles were found per day.
- When articles are available, export saves both:
  - a timeline CSV
  - an articles CSV
  packaged together in a ZIP archive.

## Behavior notes

- The app waits 20 seconds before the article search request to reduce API overload.
- A warning dialog appears for article ranges longer than 2 weeks, with options to continue or stop.
- The stop button cancels the current search and restores the UI so a new search can begin.

## Files

- `gdelt_gui_test.py` - main GUI application
- `requirements.txt` - Python dependencies
- `watch.py` - file watcher helper for development
- `notebooks/gdelt_tests.ipynb` - analysis notebook and experiments

## Troubleshooting

- If the GUI fails to start, ensure the virtual environment is activated and dependencies are installed.
- If GDELT API requests fail due to rate limiting, the app will prompt to retry immediately or wait.
- If article exports return no rows, check whether the selected date range is within the most recent GDELT article window.


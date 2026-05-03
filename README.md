# Bakery data visualisation

## Prerequisites

- **Python 3.10+** (3.11 or 3.12 recommended)
- Project data file in this folder (same directory as the scripts):

  `Data Visualisation - COM7021 - [4566] Bakery- supporting document .xlsx`

## Install dependencies

From this directory:

```bash
pip install pandas numpy openpyxl plotly dash
```

`openpyxl` is required for reading `.xlsx` in script 01.

## Run order

### 1. Clean data and build summaries

```bash
python3 01_data_cleaning_eda.py
```

This reads the workbook above, cleans it, and writes:

- `data/bakery_clean.csv` — used by the dashboard
- `data/summary_tables.xlsx` — summary tables

The `data/` folder is created automatically if it does not exist.

### 2. Interactive dashboard

```bash
python3 02_interactive_dashboard.py
```

Then open **http://127.0.0.1:8050/** in your browser.

## After changing the Excel file

Run step 1 again, then restart the dashboard (step 2) so charts use the updated CSV.

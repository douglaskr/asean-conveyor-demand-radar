# asean-conveyor-demand-radar

Production-ready Python project template for **weekly ASEAN conveyor demand intelligence**.

## What this system does

This pipeline runs weekly and performs:
1. Collects last-7-day ASEAN conveyor-related news + global risk/disaster news from GDELT.
2. Cleans and deduplicates articles.
3. Classifies by country, industry, and risk topic.
4. Scores demand signals and estimates demand pressure.
5. Stores weekly history in SQLite.
6. Exports Excel source data.
7. Generates Korean + English 7-page PPT reports.
8. Attempts PPT-to-PDF export (if LibreOffice `soffice` is installed).
9. Saves weekly outputs to `outputs/weekly/YYYY-WW/` and copies to `outputs/latest/`.
10. Logs execution to `logs/weekly_run.log`.

## Project structure

```text
config/
  countries.yaml
  industries.yaml
  global_risks.yaml
  product_mapping.yaml
  scoring_weights.yaml
  report_settings.yaml

src/
  main.py
  collectors/
  processing/
  scoring/
  reporting/
  storage/
  utils/

outputs/
  weekly/
  latest/
logs/
  weekly_run.log

data/
  radar_history.db
```

## 1) Install requirements (Windows + VS Code)

```powershell
# From repository root
python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 2) Run report manually

```powershell
.\.venv\Scripts\activate
python -m src.main
```

After running, check:
- `outputs/weekly/YYYY-WW/`
- `outputs/latest/`
- `logs/weekly_run.log`

## 3) Set Windows Task Scheduler (weekly)

1. Open **Task Scheduler** → **Create Task**.
2. **General** tab:
   - Name: `ASEAN Conveyor Weekly Radar`
   - Select "Run whether user is logged on or not".
3. **Triggers** tab:
   - New → Weekly → pick day/time (e.g., Monday 07:00).
4. **Actions** tab:
   - New → Action: "Start a program"
   - Program/script: full path to `run_weekly.bat`
     - Example: `C:\Users\<you>\projects\asean-conveyor-demand-radar\run_weekly.bat`
5. **Start in** (important): repository folder path.
6. Save and test with **Run**.

## Notes

- No API key is required for current GDELT integration.
- The pipeline is fault-tolerant: source-level failures are logged and do not stop full execution.
- For PDF export on Windows, install LibreOffice and ensure `soffice` is available in `PATH`.
- You can add new data sources by adding modules under `src/collectors/`.

# Raw source data

Raw files are not committed to this repository. Keep them in this folder for local analysis, or set `PORTFOLIO_SOURCE_DIR` to another folder containing them.

Required to run `src/prepare_data.py` and `src/fraud_model_demo.py`:

- `dataset_2026-10-26T00_59_47.261309996Z_DEFAULT_INTEGRATION_IMF.STA_FAS_8.0.0.csv`
- `Q2 2026 bulletin_Combine.xlsx` (CBN table A9)
- `PS_20174392719_1491204439457_log.csv.zip` (synthetic PaySim transactions)

For source verification of the manually transcribed Ghana fraud summary:

- `BANKS-SDIs-PSPs-2023-FRAUD-REPORT.pdf`
- `NOTICE-NO.-BG-GOV-SEC-2025-09-Publication-of-Banks-SDIS-and-PSPS-2024-Fraud-Report-1.pdf`

The companion CBN narrative PDF is useful for manual context, but not read by the script. The duplicate workbook and unrelated teaching-plan PDF are excluded.

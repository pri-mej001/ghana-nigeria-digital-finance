# Ghana–Nigeria Digital Finance: Growth, Access, and Fraud Risk

A reproducible portfolio analysis for fintech and payments stakeholders. It examines payment activity, access indicators, Ghana fraud-report trends, and a separate synthetic fraud-detection demonstration.

## Start here

- Open [visualizations/index.html](visualizations/index.html) in a browser for the dashboard.
- Read [management_brief.md](management_brief.md) for the management interpretation and caveats.
- Read [outputs/initial_data_review.md](outputs/initial_data_review.md) for source coverage and data-quality notes.
- Review the scripts in [src/](src/) for extraction, aggregation, and modeling logic.

## Data and reproducibility

Raw source files are not included. Obtain the listed source files from their publishers or your authorized source folder, place them in data/raw/, then run:

```powershell
python -m pip install -r requirements.txt
python .\src\prepare_data.py
python .\src\fraud_model_demo.py
```

Alternatively, point the scripts at another folder with the PORTFOLIO_SOURCE_DIR environment variable. Required filenames are listed in data/raw/README.md.

The scripts write derived CSVs and the initial review into outputs/. They do not modify source files. The visualization is a standalone HTML file and does not require a Python charting library.

## Evidence boundaries

- IMF mobile-money transaction intensity is not a unique-customer count or an adult-inclusion rate.
- CBN payment rails have different definitions and coverage; CBN notes intra-bank activity is included from 2020. The 2026 observations are partial.
- Ghana 2023 fraud amounts are described as reported loss; 2024 amounts are value at risk. Do not treat them as a comparable year-over-year money series.
- PaySim is synthetic. Its model scores illustrate workflow and alert trade-offs, not Ghanaian or Nigerian provider performance.
- The Nigeria IMF mobile-money series has a sharp 2023 increase that requires source-continuity validation.
- Aggregate associations do not establish that fraud caused a change in payment adoption or growth.

## Project layout

```text
src/              extraction and synthetic modeling scripts
outputs/          derived tables, metrics, and analysis notes
data/raw/         local source files (not committed)
visualizations/   standalone dashboard
```

## Data sources

The pipeline expects an IMF Financial Access Survey extract, a CBN quarterly statistical bulletin workbook, the BoG 2023 and 2024 banks/SDIs/PSPs fraud reports, and the synthetic PaySim transaction archive. Consult data/raw/README.md for exact expected filenames and source handling.

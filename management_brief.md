# Management brief: Ghana–Nigeria digital finance

## What the evidence says

- **Payment activity is growing.** CBN Mobile Pay volume rose from 1.86 billion transactions in 2022 to 8.64 billion in 2025 (+364%). This is activity in a payment rail, not a count of unique customers. CBN notes that its captured payment data includes intra-bank transactions from 2020 onward, so long-run changes cross a measurement break.
- **Digital access is advancing, but activity is not the same as inclusion.** IMF FAS reports 2025 mobile-money transaction intensity of 428,588 per 1,000 adults in Ghana and 203,436 in Nigeria. The Nigeria series jumps sharply in 2023. Verify its continuity and definitions before drawing a growth conclusion; transaction intensity cannot establish how many distinct adults use the service.
- **Fraud is a material operating risk.** Ghana PSP reported cases rose from 14,655 in 2023 to 15,673 in 2024; bank cases fell from 969 to 716 while card/ATM/POS cases rose from 218 to 413. The reports do not show that fraud caused or slowed payment growth.
- **The reported money measures need separate treatment.** Ghana's 2024 report gives value at risk of GH¢75m for banks, GH¢4.5m for SDIs and GH¢19m for PSPs. The 2023 report calls its money measure reported loss, so the amounts are not plotted as a comparable two-year trend.
- **A detection model needs a workload discussion.** On synthetic PaySim data, a time-split baseline achieved 82.7% recall at 8.3% precision and a 14.3% false-positive rate. That demonstrates the trade-off between catching fraud and reviewing false alerts; it is not evidence about a Ghanaian or Nigerian fintech.

## Recommended management interpretation

Treat payment growth as a commercial opportunity and fraud handling as a parallel operating capability. Track adoption with distinct active customers and retention, payments with rail-specific volumes and values, and fraud with consistent definitions for cases, value at risk, confirmed loss, recovery and customer impact. Do not infer that fraud is the cause of adoption or growth changes from these aggregate sources.

## Next single step

Build a source-definition register with the business owner for each indicator: definition, period, reporting break, unit, and whether the measure is a count, value, rate or unique-customer measure. Resolve the Nigeria 2023 mobile-money discontinuity and align Ghana fraud monetary definitions before turning these visuals into final portfolio claims.

## Files

- Interactive chart dashboard: `visualizations/index.html`
- Reproducible extracts and source review: `outputs\`
- PaySim baseline code and metrics: `src\fraud_model_demo.py`, `outputs\paysim_baseline_metrics.csv`

Raw data files are excluded from the repository; only the derived analysis outputs are included. The source files were not modified.


# Ghana–Nigeria Digital Finance: Growth, Access, and Fraud Risk

A reproducible portfolio analysis of digital finance in Ghana and Nigeria, covering access, payment growth, reported fraud, and a separate synthetic fraud-detection demonstration.

## Open the dashboard

[Launch the interactive dashboard](https://pri-mej001.github.io/ghana-nigeria-digital-finance/) and use the country, measure, year, and sector slicers to explore the charts.

Dashboard code: [visualizations/index.html](visualizations/index.html).

## Project guide

- [Management brief](management_brief.md): findings, interpretation, and limits.
- [Data review](outputs/initial_data_review.md): source inventory and data-quality notes.
- [Analysis scripts](src/): preparation, summaries, and fraud demo.

## Data and reproducibility

Raw source files are not included. Obtain source datasets from their publishers or your authorized source folder, place them in data/raw/, then follow the commands in the project documentation. Derived summaries and visualizations are provided where licensing permits.

## Evidence limits

The country comparisons use distinct datasets and definitions; charts are descriptive context, not a harmonized causal comparison. The PaySim fraud model uses synthetic mobile-money transactions and is a methods demonstration, not a validated detector for Ghana or Nigeria.

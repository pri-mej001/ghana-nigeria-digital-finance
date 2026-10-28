"""Create read-only source extracts for the Ghana–Nigeria digital-finance project."""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path(os.environ.get("PORTFOLIO_SOURCE_DIR", str(PROJECT_DIR / "data" / "raw")))
OUTPUT_DIR = PROJECT_DIR / "outputs"
FAS_NAME = "dataset_2026-10-26T00_59_47.261309996Z_DEFAULT_INTEGRATION_IMF.STA_FAS_8.0.0.csv"
CBN_NAME = "Q2 2026 bulletin_Combine.xlsx"
PAYSIM_NAME = "PS_20174392719_1491204439457_log.csv.zip"

# Exact country-indicator-series combinations selected after checking unit,
# coverage, and raw-vs-normalized duplicates in the IMF FAS source.
FAS_SERIES = {
    ("Ghana", "Active mobile money accounts", "GHA.FA63._Z._Z._T.NUM.A"),
    ("Ghana", "Active mobile money accounts", "GHA.FA63._Z._Z._T.PTADLT_NUM.A"),
    ("Nigeria", "Active mobile money accounts", "NGA.FA63._Z._Z._T.NUM.A"),
    ("Nigeria", "Active mobile money accounts", "NGA.FA63._Z._Z._T.PTADLT_NUM.A"),
    ("Ghana", "Registered mobile money accounts", "GHA.FA67._Z._Z._T.NUM.A"),
    ("Ghana", "Registered mobile money accounts", "GHA.FA67._Z._Z._T.PTADLT_NUM.A"),
    ("Nigeria", "Registered mobile money accounts", "NGA.FA67._Z._Z._T.NUM.A"),
    ("Nigeria", "Registered mobile money accounts", "NGA.FA67._Z._Z._T.PTADLT_NUM.A"),
    ("Ghana", "Active mobile money agent outlets", "GHA.FA5._Z._Z._T.NUM.A"),
    ("Ghana", "Active mobile money agent outlets", "GHA.FA5._Z._Z._T.PTKM2_NUM.A"),
    ("Nigeria", "Active mobile money agent outlets", "NGA.FA5._Z._Z._T.NUM.A"),
    ("Ghana", "Mobile money transactions (during the reference year)", "GHA.FA66._Z._Z._T.NUM.A"),
    ("Ghana", "Mobile money transactions (during the reference year)", "GHA.FA66._Z._Z._T.PTADLT_NUM.A"),
    ("Nigeria", "Mobile money transactions (during the reference year)", "NGA.FA66._Z._Z._T.NUM.A"),
    ("Nigeria", "Mobile money transactions (during the reference year)", "NGA.FA66._Z._Z._T.PTADLT_NUM.A"),
    ("Ghana", "Value of mobile money transactions (during the reference year)", "GHA.FA65._Z._Z._T.XDC.A"),
    ("Ghana", "Value of mobile money transactions (during the reference year)", "GHA.FA65._Z._Z._T.POGDP.A"),
    ("Nigeria", "Value of mobile money transactions (during the reference year)", "NGA.FA65._Z._Z._T.XDC.A"),
    ("Nigeria", "Value of mobile money transactions (during the reference year)", "NGA.FA65._Z._Z._T.POGDP.A"),
    ("Ghana", "Mobile and internet banking transactions (during the reference year)", "GHA.FA35.COMBANK._Z._T.NUM.A"),
    ("Ghana", "Mobile and internet banking transactions (during the reference year)", "GHA.FA35.COMBANK._Z._T.XDC.A"),
    ("Nigeria", "Mobile and internet banking transactions (during the reference year)", "NGA.FA35.COMBANK._Z._T.NUM.A"),
    ("Nigeria", "Mobile and internet banking transactions (during the reference year)", "NGA.FA35.COMBANK._Z._T.XDC.A"),
    ("Ghana", "Depositors", "GHA.FA29._Z.COMBANK._T.NUM.A"),
    ("Ghana", "Depositors", "GHA.FA29._Z.COMBANK._T.PTADLT_NUM.A"),
    ("Nigeria", "Depositors", "NGA.FA29._Z.COMBANK._T.NUM.A"),
    ("Nigeria", "Depositors", "NGA.FA29._Z.COMBANK._T.PTADLT_NUM.A"),
}


def require_sources() -> None:
    for name in (FAS_NAME, CBN_NAME, PAYSIM_NAME):
        if not (SOURCE_DIR / name).is_file():
            raise FileNotFoundError(f"Required source file not found: {SOURCE_DIR / name}")


def make_fas_extract() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(SOURCE_DIR / FAS_NAME, low_memory=False)
    for column in ["DATASET", "SERIES_CODE", "OBS_MEASURE", "COUNTRY", "INDICATOR", "SECTOR",
                   "COUNTERPARTY_SECTOR", "SEX", "TYPE_OF_TRANSFORMATION", "FREQUENCY", "SCALE", "UNIT"]:
        raw[column] = raw[column].astype("string").str.strip()
    id_cols = [
        "DATASET", "SERIES_CODE", "OBS_MEASURE", "COUNTRY", "INDICATOR", "SECTOR",
        "COUNTERPARTY_SECTOR", "SEX", "TYPE_OF_TRANSFORMATION", "FREQUENCY", "SCALE", "UNIT",
    ]
    year_cols = [c for c in raw.columns if str(c).isdigit()]
    keys = list(zip(raw["COUNTRY"], raw["INDICATOR"], raw["SERIES_CODE"]))
    selected = raw.loc[[key in FAS_SERIES for key in keys], id_cols + year_cols].copy()
    long = selected.melt(id_vars=id_cols, var_name="year", value_name="value")
    long["year"] = long["year"].astype(int)
    long = long.dropna(subset=["value"]).sort_values(["COUNTRY", "INDICATOR", "SERIES_CODE", "year"])
    long = long.rename(columns={"COUNTRY": "country", "INDICATOR": "indicator", "SERIES_CODE": "series_code"})
    long.to_csv(OUTPUT_DIR / "fas_ghana_nigeria_core_long.csv", index=False)
    coverage = (
        long.groupby(["country", "indicator", "series_code", "TYPE_OF_TRANSFORMATION", "SCALE", "UNIT"], as_index=False, dropna=False)
        .agg(first_year=("year", "min"), last_year=("year", "max"), observations=("value", "count"))
    )
    coverage.to_csv(OUTPUT_DIR / "fas_series_coverage.csv", index=False)
    return long, coverage


def make_cbn_extract() -> pd.DataFrame:
    book = pd.ExcelFile(SOURCE_DIR / CBN_NAME)
    if "A9" not in book.sheet_names:
        raise ValueError("CBN workbook does not contain expected payments table A9")
    table = pd.read_excel(SOURCE_DIR / CBN_NAME, sheet_name="A9", header=None)
    rails = [str(x).strip() for x in table.iloc[2, 1::2].tolist()]
    records: list[dict[str, object]] = []
    for _, row in table.iloc[4:].iterrows():
        period = row.iloc[0]
        if not isinstance(period, pd.Timestamp) and not hasattr(period, "year"):
            continue
        for rail_index, rail in enumerate(rails):
            volume = row.iloc[1 + rail_index * 2]
            value = row.iloc[2 + rail_index * 2]
            records.append({"month": pd.Timestamp(period).strftime("%Y-%m"), "rail": rail,
                            "volume": pd.to_numeric(volume, errors="coerce"),
                            "value_ngn_million": pd.to_numeric(value, errors="coerce")})
    out = pd.DataFrame.from_records(records)
    out.to_csv(OUTPUT_DIR / "cbn_payments_monthly_long.csv", index=False)
    return out


def make_cbn_annual(cbn: pd.DataFrame) -> pd.DataFrame:
    annual = cbn.copy()
    annual["year"] = annual["month"].str[:4].astype(int)
    out = annual.groupby(["rail", "year"], as_index=False).agg(
        months_with_volume=("volume", "count"),
        volume=("volume", lambda values: values.sum(min_count=1)),
        months_with_value=("value_ngn_million", "count"),
        value_ngn_million=("value_ngn_million", lambda values: values.sum(min_count=1)),
    )
    out.to_csv(OUTPUT_DIR / "cbn_payments_annual.csv", index=False)
    return out


def make_paysim_profile() -> pd.DataFrame:
    # Aggregate in chunks so the 186 MB archive is not expanded or loaded whole.
    totals: dict[str, dict[str, float]] = {}
    with zipfile.ZipFile(SOURCE_DIR / PAYSIM_NAME) as archive:
        member = next(name for name in archive.namelist() if name.lower().endswith(".csv"))
        with archive.open(member) as stream:
            for chunk in pd.read_csv(stream, chunksize=500_000):
                for transaction_type, rows in chunk.groupby("type"):
                    acc = totals.setdefault(str(transaction_type), {"transactions": 0, "fraud_cases": 0,
                                                                       "transaction_amount": 0, "fraud_amount": 0})
                    fraud = rows["isFraud"].eq(1)
                    acc["transactions"] += len(rows)
                    acc["fraud_cases"] += int(fraud.sum())
                    acc["transaction_amount"] += float(rows["amount"].sum())
                    acc["fraud_amount"] += float(rows.loc[fraud, "amount"].sum())
    records = []
    for transaction_type, values in sorted(totals.items()):
        records.append({"transaction_type": transaction_type, **values,
                        "fraud_rate": values["fraud_cases"] / values["transactions"]})
    profile = pd.DataFrame(records)
    profile.to_csv(OUTPUT_DIR / "paysim_synthetic_profile_by_type.csv", index=False)
    return profile


def make_ghana_fraud_context() -> pd.DataFrame:
    report23 = "BANKS-SDIs-PSPs-2023-FRAUD-REPORT.pdf"
    report24 = "NOTICE-NO.-BG-GOV-SEC-2025-09-Publication-of-Banks-SDIS-and-PSPS-2024-Fraud-Report-1.pdf"
    records = [
        (2023, "Banks", 969, 63.0, "reported loss", report23, "pp. 9-10"),
        (2023, "SDIs", 241, 8.7, "reported loss", report23, "pp. 13-14"),
        (2023, "PSPs", 14655, 16.0, "reported loss", report23, "pp. 16-17"),
        (2024, "Banks", 716, 75.0, "value at risk", report24, "pp. 11-12"),
        (2024, "SDIs", 344, 4.5, "value at risk", report24, "pp. 15-16"),
        (2024, "PSPs", 15673, 19.0, "value at risk", report24, "pp. 20-21"),
    ]
    out = pd.DataFrame(records, columns=["year", "sector", "reported_cases", "reported_amount_ghs_million",
                                         "amount_measure", "source_file", "source_location"])
    out.to_csv(OUTPUT_DIR / "ghana_fraud_context.csv", index=False)
    return out


def make_data_quality_flags(fas: pd.DataFrame, cbn_annual: pd.DataFrame) -> pd.DataFrame:
    flags = [
        {"source": "IMF FAS", "severity": "high", "issue": "Nigeria active mobile-money accounts end in 2023",
         "impact": "No 2024-2025 comparison of active accounts is available for Nigeria in this extract."},
        {"source": "IMF FAS", "severity": "high", "issue": "Nigeria mobile-money transactions per 1,000 adults rise about 5.4x from 2022 to 2023",
         "impact": "Confirm reporting continuity and source notes before presenting the trend as an underlying market acceleration."},
        {"source": "IMF FAS", "severity": "high", "issue": "Nigeria registered mobile-money accounts rise about 143% from 2024 to 2025",
         "impact": "Validate the latest observation and definitions; account totals are not unique customers."},
        {"source": "CBN Statistical Bulletin", "severity": "high", "issue": "Payment-system statistics include intra-bank transactions from 2020",
         "impact": "Interpret long-term growth with this source-defined break in mind."},
        {"source": "CBN Statistical Bulletin", "severity": "high", "issue": "NIP has missing 2021-2024 months in A9 and resumes in 2025",
         "impact": "Do not treat absent monthly values as zero or calculate a continuous NIP trend across the gap."},
        {"source": "CBN Statistical Bulletin", "severity": "medium", "issue": "2026 payment observations run only through March",
         "impact": "2026 is a partial year and must not be compared with full-year totals."},
        {"source": "Bank of Ghana Fraud Reports", "severity": "high", "issue": "2023 report uses loss-value language; 2024 report reports value at risk",
         "impact": "Avoid a direct year-over-year monetary fraud comparison without reconciled definitions."},
        {"source": "PaySim", "severity": "high", "issue": "Transaction labels are synthetic and highly imbalanced",
         "impact": "Model metrics demonstrate workflow only and do not estimate fraud detection performance in Ghana or Nigeria."},
    ]
    out = pd.DataFrame(flags)
    out.to_csv(OUTPUT_DIR / "data_quality_flags.csv", index=False)
    return out


def create_findings(fas: pd.DataFrame, coverage: pd.DataFrame, cbn: pd.DataFrame,
                    annual: pd.DataFrame, paysim: pd.DataFrame) -> None:
    mobile_adult = fas[fas["series_code"].isin([
        "GHA.FA66._Z._Z._T.PTADLT_NUM.A", "NGA.FA66._Z._Z._T.PTADLT_NUM.A"
    ])]
    mobile_adult_2025 = {
        row["country"]: float(row["value"])
        for _, row in mobile_adult[mobile_adult["year"].eq(2025)].iterrows()
    }
    mobile_pay_annual = annual[(annual["rail"].eq("Mobile Pay")) & annual["year"].isin([2022, 2025])]
    mobile_pay_2022 = mobile_pay_annual.loc[mobile_pay_annual.year.eq(2022), "volume"].iloc[0]
    mobile_pay_2025 = mobile_pay_annual.loc[mobile_pay_annual.year.eq(2025), "volume"].iloc[0]
    mobile_pay_growth = mobile_pay_2025 / mobile_pay_2022 - 1
    lines = [
        "# Initial Data Review",
        "",
        "This note records what the supplied files support before deeper analysis. It is generated by `src/prepare_data.py`.",
        "",
        "## IMF Financial Access Survey",
        "",
        f"The source contains {len(fas):,} non-missing annual observations for the selected Ghana/Nigeria series across {fas['year'].nunique()} years. The extract keeps raw levels separate from adult-normalized rates, geographic-density rates, domestic-currency values, and GDP shares.",
        "",
        "Key coverage limitation: Ghana has active mobile money account counts through 2025 in this extract, but Nigeria's active mobile money account series is only present for 2021–2023. Nigeria registered-account counts and transaction counts/value continue later, but these are different measures and must not be substituted for active accounts.",
        "",
        "For comparisons, prefer common annual series and use the IMF per-1,000-adults measures when present. Keep raw account counts for country-level scale context only. Check the metadata and source release before interpreting the 2025 values as complete.",
        "",
        "## Initial management readout",
        "",
        f"The IMF FAS reports {mobile_adult_2025.get('Ghana', float('nan')):,.0f} Ghana and {mobile_adult_2025.get('Nigeria', float('nan')):,.0f} Nigeria mobile-money transactions per 1,000 adults in 2025. This is transaction intensity, not the share of adults using mobile money. Nigeria's normalized series rises sharply between 2022 and 2023, so confirm the source definition and reporting continuity before presenting comparative growth.",
        f"CBN's Nigeria `Mobile Pay` channel recorded {mobile_pay_2022:,.0f} transactions in 2022 and {mobile_pay_2025:,.0f} in 2025 ({mobile_pay_growth:.0%} transaction-volume growth). This describes activity in one domestic payment system and should not be read as unique customers or compared directly to IMF mobile-money totals without reconciling definitions.",
        "",
        "## Nigeria payment-system series",
        "",
        f"CBN table A9 yields {len(cbn):,} rail-month records across {cbn['rail'].nunique()} payment rails, from {cbn['month'].min()} to {cbn['month'].max()}. Volumes and values are kept separate; `n. a.` remains missing rather than becoming zero. Annual summaries include the count of months with data so partial years remain visible.",
        "",
        "The table footnote states that from 2020 the captured data includes intra-bank transactions. Treat that as a measurement break when interpreting long-run growth. Nigeria-only payment infrastructure here does not establish a direct Ghana-vs-Nigeria rail comparison.",
        "",
        "## Ghana fraud reports",
        "",
        "Bank of Ghana reported cases sum consistently by sector: banks fell from 969 to 716, SDIs rose from 241 to 344, and PSPs rose from 14,655 to 15,673 between 2023 and 2024. Bank card/ATM/POS cases rose from 218 in 2023 to 413 in 2024 (+89%), even as total bank cases fell. The 2024 report attributes risks to increased digital-channel use and customer understanding, but these reports do not establish a causal effect on payment adoption or market growth.",
        "",
        "The 2023 report describes amounts as reported loss; the 2024 report describes amounts as value at risk. The 2024 report gives GH¢75m for banks, GH¢4.5m for SDIs and GH¢19m for PSPs. Keep these measures distinct unless their definitions are reconciled. Forgery/document manipulation accounts for 67% of 2024 banks-and-SDIs value at risk. The reports support fraud as a management risk, but not a measured growth penalty.",
        "",
        "## Synthetic fraud dataset",
        "",
        f"The zipped transaction file has fields `step`, transaction `type`, `amount`, origin/destination account IDs and balances, `isFraud`, and `isFlaggedFraud`. The profile covers {int(paysim['transactions'].sum()):,} simulated transactions and {int(paysim['fraud_cases'].sum()):,} labeled fraud cases ({paysim['fraud_cases'].sum() / paysim['transactions'].sum():.4%}). A time-split logistic baseline is built from pre-transaction features; its estimated test precision is low at the threshold chosen to capture 80% of validation fraud. This illustrates the detection/false-alarm trade-off, not local fintech performance.",
        "",
        "## Next project milestone",
        "",
        "Settle the comparison indicators and periods, then create a management view that puts access and payments growth beside the Ghana fraud-risk trend. Keep the synthetic fraud-model experiment in a separate methods section and label it clearly.",
        "",
        "## Extract coverage",
        "",
        f"Selected IMF series: {len(coverage)}. Nigeria CBN payment rails: {', '.join(sorted(cbn['rail'].unique()))}.",
    ]
    (OUTPUT_DIR / "initial_data_review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    require_sources()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fas, coverage = make_fas_extract()
    cbn = make_cbn_extract()
    annual = make_cbn_annual(cbn)
    paysim = make_paysim_profile()
    make_ghana_fraud_context()
    make_data_quality_flags(fas, annual)
    create_findings(fas, coverage, cbn, annual, paysim)
    print(f"Wrote {len(fas):,} IMF observations, {len(coverage):,} series coverage rows, {len(cbn):,} CBN payment-rail months, {len(annual):,} annual rail summaries, and {int(paysim['transactions'].sum()):,} PaySim rows to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()


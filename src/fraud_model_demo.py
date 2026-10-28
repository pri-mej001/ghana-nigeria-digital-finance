"""Train a time-split logistic baseline on the synthetic PaySim file only.

This is a methods demonstration, not a Ghana/Nigeria fraud model. It uses only
pre-transaction variables and never uses isFlaggedFraud or post-transaction
balances as predictors. Non-fraud rows are sampled at a fixed rate; weighted
evaluation corrects for that sampling.
"""

from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path(os.environ.get("PORTFOLIO_SOURCE_DIR", str(PROJECT_DIR / "data" / "raw")))
SOURCE_FILE = SOURCE_DIR / "PS_20174392719_1491204439457_log.csv.zip"
OUTPUT_DIR = PROJECT_DIR / "outputs"
NEGATIVE_SAMPLE_RATE = 0.10
SEED = 73
TYPE_NAMES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]


def features(frame: pd.DataFrame) -> np.ndarray:
    amount = np.log1p(frame["amount"].clip(lower=0).to_numpy(dtype=np.float64))
    origin = np.log1p(frame["oldbalanceOrg"].clip(lower=0).to_numpy(dtype=np.float64))
    destination = np.log1p(frame["oldbalanceDest"].clip(lower=0).to_numpy(dtype=np.float64))
    step = frame["step"].to_numpy(dtype=np.float64)
    types = np.column_stack([(frame["type"].to_numpy() == name).astype(np.float64) for name in TYPE_NAMES])
    return np.column_stack([amount, origin, destination, step, types])


def collect_splits() -> tuple[tuple[np.ndarray, np.ndarray], ...]:
    rng = np.random.default_rng(SEED)
    blocks: dict[str, list[tuple[np.ndarray, np.ndarray]]] = {"train": [], "validation": [], "test": []}
    with zipfile.ZipFile(SOURCE_FILE) as archive:
        member = next(name for name in archive.namelist() if name.lower().endswith(".csv"))
        with archive.open(member) as stream:
            for chunk in pd.read_csv(stream, chunksize=350_000):
                group_masks = {
                    "train": chunk["step"].le(500),
                    "validation": chunk["step"].between(501, 600),
                    "test": chunk["step"].gt(600),
                }
                fraud = chunk["isFraud"].eq(1)
                for split, mask in group_masks.items():
                    candidates = chunk.loc[mask]
                    labels = fraud.loc[candidates.index]
                    keep = labels | (rng.random(len(candidates)) < NEGATIVE_SAMPLE_RATE)
                    selected = candidates.loc[keep]
                    if len(selected):
                        blocks[split].append((features(selected), selected["isFraud"].to_numpy(dtype=np.float64)))
    result = []
    for split in ("train", "validation", "test"):
        xs = np.vstack([x for x, _ in blocks[split]])
        ys = np.concatenate([y for _, y in blocks[split]])
        result.append((xs, ys))
    return tuple(result)


def sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.clip(z, -35, 35)
    return 1.0 / (1.0 + np.exp(-z))


def fit_logistic(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale[scale == 0] = 1
    z = (x - mean) / scale
    weights = np.where(y == 1, 1.0, 1.0 / NEGATIVE_SAMPLE_RATE)
    weights /= weights.mean()
    beta = np.zeros(z.shape[1], dtype=np.float64)
    rng = np.random.default_rng(SEED)
    batch_size = 60_000
    for epoch in range(18):
        order = rng.permutation(len(y))
        rate = 0.08 / (1 + epoch * 0.08)
        for start in range(0, len(y), batch_size):
            idx = order[start:start + batch_size]
            p = sigmoid(z[idx] @ beta)
            gradient = (z[idx].T @ ((p - y[idx]) * weights[idx])) / weights[idx].sum()
            gradient[1:] += 0.0005 * beta[1:]
            beta -= rate * gradient
    return beta, mean, scale


def weighted_metrics(y: np.ndarray, score: np.ndarray, threshold: float) -> dict[str, float]:
    sample_weight = np.where(y == 1, 1.0, 1.0 / NEGATIVE_SAMPLE_RATE)
    pred = score >= threshold
    tp = float(sample_weight[(y == 1) & pred].sum())
    fp = float(sample_weight[(y == 0) & pred].sum())
    fn = float(sample_weight[(y == 1) & ~pred].sum())
    tn = float(sample_weight[(y == 0) & ~pred].sum())
    recall = tp / (tp + fn) if tp + fn else 0
    precision = tp / (tp + fp) if tp + fp else 0

    order = np.argsort(score, kind="mergesort")
    sorted_score, sorted_y, sorted_w = score[order], y[order], sample_weight[order]
    auc_num = 0.0
    neg_before = 0.0
    i = 0
    while i < len(sorted_score):
        j = i + 1
        while j < len(sorted_score) and sorted_score[j] == sorted_score[i]:
            j += 1
        group_pos = float(sorted_w[i:j][sorted_y[i:j] == 1].sum())
        group_neg = float(sorted_w[i:j][sorted_y[i:j] == 0].sum())
        auc_num += group_pos * (neg_before + 0.5 * group_neg)
        neg_before += group_neg
        i = j
    total_pos = float(sample_weight[y == 1].sum())
    total_neg = float(sample_weight[y == 0].sum())
    roc_auc = auc_num / (total_pos * total_neg) if total_pos and total_neg else float("nan")

    desc = np.argsort(-score, kind="mergesort")
    sorted_y, sorted_w = y[desc], sample_weight[desc]
    cum_tp = np.cumsum(sorted_w * sorted_y)
    cum_fp = np.cumsum(sorted_w * (1 - sorted_y))
    prec = cum_tp / np.maximum(cum_tp + cum_fp, 1e-12)
    rec = cum_tp / max(total_pos, 1e-12)
    ap = float(np.sum(np.diff(np.r_[0, rec]) * prec))
    return {"threshold": float(threshold), "precision": precision, "recall": recall,
            "false_positive_rate": fp / (fp + tn) if fp + tn else 0,
            "roc_auc": roc_auc, "average_precision": ap,
            "weighted_true_positives": tp, "weighted_false_positives": fp}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (x_train, y_train), (x_val, y_val), (x_test, y_test) = collect_splits()
    beta, mean, scale = fit_logistic(x_train, y_train)
    val_scores = sigmoid(((x_val - mean) / scale) @ beta)
    # Choose a validation threshold that captures at least 80% of positive cases.
    positive_scores = val_scores[y_val == 1]
    threshold = float(np.quantile(positive_scores, 0.20))
    test_scores = sigmoid(((x_test - mean) / scale) @ beta)
    metrics = weighted_metrics(y_test, test_scores, threshold)
    metrics.update({
        "model": "logistic_regression",
        "data": "synthetic PaySim",
        "train_sample_rows": int(len(y_train)),
        "validation_sample_rows": int(len(y_val)),
        "test_sample_rows": int(len(y_test)),
        "train_sample_fraud_rows": int(y_train.sum()),
        "validation_sample_fraud_rows": int(y_val.sum()),
        "test_sample_fraud_rows": int(y_test.sum()),
        "negative_sampling_rate": NEGATIVE_SAMPLE_RATE,
        "time_split": "train step<=500; validation 501-600; test >600",
        "feature_names": json.dumps(["log_amount", "log_oldbalanceOrg", "log_oldbalanceDest", "step", *TYPE_NAMES]),
        "coefficients_standardized": json.dumps(beta.tolist()),
        "warning": "Synthetic-data demonstration only; not validated on Ghana or Nigeria transaction records.",
    })
    pd.DataFrame([metrics]).to_csv(OUTPUT_DIR / "paysim_baseline_metrics.csv", index=False)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()




from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

from src.inventory_data import DATA_DIR, REPORTS_DIR
from src.inventory_train import MODELS_DIR


def mape(y_true: pd.Series, pred: np.ndarray) -> float:
    denom = np.maximum(np.asarray(y_true), 1)
    return float(np.mean(np.abs((np.asarray(y_true) - pred) / denom)) * 100)


def evaluate_model() -> dict[str, float]:
    model_path = MODELS_DIR / "inventory_model.joblib"
    test_path = DATA_DIR / "inventory_test.csv"
    data = pd.read_csv(test_path)
    data["date"] = pd.to_datetime(data["date"])
    data["day_of_week"] = data["date"].dt.dayofweek

    features = ["store_id", "sku_id", "stock_qty", "sales_qty", "delivery_qty", "day_of_week"]
    target = "stock_qty_next_day"

    model = joblib.load(model_path)
    pred = np.maximum(model.predict(data[features]), 0)
    base_pred = (data["stock_qty"] - data["sales_qty"] + data["delivery_qty"]).clip(lower=0)

    result = {
        "new_rmse": float(np.sqrt(mean_squared_error(data[target], pred))),
        "baseline_rmse": float(np.sqrt(mean_squared_error(data[target], base_pred))),
        "new_mape": mape(data[target], pred),
        "baseline_mape": mape(data[target], base_pred.to_numpy()),
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "model_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines = [
        "Generated at: 2026-05-24 17:22:41 MSK",
        "",
        "# Model metrics",
        "",
        f"- new_mape: `{result['new_mape']:.3f}`",
        f"- baseline_mape: `{result['baseline_mape']:.3f}`",
        f"- new_rmse: `{result['new_rmse']:.3f}`",
        f"- baseline_rmse: `{result['baseline_rmse']:.3f}`",
        "",
        "**Вывод:** новая модель сравнивается с baseline, без этого registry не обновляем.",
        "",
    ]
    (REPORTS_DIR / "model_metrics.md").write_text("\n".join(lines), encoding="utf-8")
    return result


def compare_with_baseline(max_mape: float = 15.0) -> str:
    metrics = json.loads((REPORTS_DIR / "model_metrics.json").read_text(encoding="utf-8"))
    ok = metrics["new_mape"] <= max_mape and metrics["new_mape"] <= metrics["baseline_mape"]
    branch = "register_model" if ok else "skip_deploy"
    lines = [
        "Generated at: 2026-05-24 17:22:41 MSK",
        "",
        "# Compare task log",
        "",
        f"- policy: `new_mape <= {max_mape}` and `new_mape <= baseline_mape`",
        f"- new_mape: `{metrics['new_mape']:.3f}`",
        f"- baseline_mape: `{metrics['baseline_mape']:.3f}`",
        f"- branch: `{branch}`",
        "",
        "**Вывод:** BranchPythonOperator отправляет run в register или skip.",
        "",
    ]
    (REPORTS_DIR / "airflow_compare_log.md").write_text("\n".join(lines), encoding="utf-8")
    return branch

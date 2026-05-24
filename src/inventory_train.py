from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.inventory_data import DATA_DIR, REPORTS_DIR, load_inventory


ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"


def split_data(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    border = data["date"].quantile(0.8)
    train = data[data["date"] <= border].copy()
    test = data[data["date"] > border].copy()
    return train, test


def train_model(data_path: Path | None = None) -> dict[str, object]:
    data = load_inventory(data_path)
    data["day_of_week"] = data["date"].dt.dayofweek
    train, test = split_data(data)

    features = ["store_id", "sku_id", "stock_qty", "sales_qty", "delivery_qty", "day_of_week"]
    target = "stock_qty_next_day"

    model = Pipeline(
        steps=[
            (
                "prep",
                ColumnTransformer(
                    transformers=[
                        ("cat", OneHotEncoder(handle_unknown="ignore"), ["store_id", "sku_id"]),
                        ("num", "passthrough", ["stock_qty", "sales_qty", "delivery_qty", "day_of_week"]),
                    ]
                ),
            ),
            ("model", LinearRegression()),
        ]
    )
    model.fit(train[features], train[target])

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / "inventory_model.joblib"
    joblib.dump(model, model_path)

    test_path = DATA_DIR / "inventory_test.csv"
    test.to_csv(test_path, index=False)

    run = {
        "run_id": datetime.utcnow().strftime("run_%Y%m%d_%H%M%S"),
        "model_path": str(model_path),
        "test_path": str(test_path),
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "features": features,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "train_run.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
    return run

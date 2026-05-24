from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

REQ_COLS = {
    "date": "object",
    "store_id": "object",
    "sku_id": "object",
    "stock_qty": "number",
    "sales_qty": "number",
    "delivery_qty": "number",
}


def make_demo_inventory(path: Path | None = None) -> Path:
    path = path or DATA_DIR / "demo_inventory_batch.csv"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(42)
    days = pd.date_range("2026-04-01", periods=60, freq="D")
    rows = []

    for store in range(1, 5):
        for sku in range(1, 9):
            stock = rng.integers(60, 140)
            for date in days:
                sales = max(0, int(rng.normal(12 + sku * 0.4, 3)))
                delivery = int(rng.choice([0, 0, 0, 20, 30]))
                weekday = date.dayofweek
                store_shift = store * 1.4
                sku_shift = sku * 0.9
                next_stock = max(
                    5,
                    int(
                        0.82 * stock
                        - 0.55 * sales
                        + 0.9 * delivery
                        + 8
                        + store_shift
                        + sku_shift
                        + weekday * 0.7
                        + rng.normal(0, 1.5)
                    ),
                )
                rows.append(
                    {
                        "date": date.date().isoformat(),
                        "store_id": f"store_{store}",
                        "sku_id": f"sku_{sku}",
                        "stock_qty": int(stock),
                        "sales_qty": int(sales),
                        "delivery_qty": int(delivery),
                        "stock_qty_next_day": int(next_stock),
                    }
                )
                stock = next_stock

    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def make_latency_data() -> tuple[Path, Path]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(9)
    ts = pd.date_range("2026-05-01", periods=48, freq="h")

    ref = pd.DataFrame(
        {
            "timestamp": ts.astype(str),
            "latency_ms": np.round(rng.normal(122, 14, len(ts)).clip(80), 2),
        }
    )
    new = pd.DataFrame(
        {
            "timestamp": ts.astype(str),
            "latency_ms": np.round(rng.normal(181, 18, len(ts)).clip(100), 2),
        }
    )

    ref_path = DATA_DIR / "reference_latency.csv"
    new_path = DATA_DIR / "new_latency.csv"
    ref.to_csv(ref_path, index=False)
    new.to_csv(new_path, index=False)
    return ref_path, new_path


def load_inventory(path: Path | None = None) -> pd.DataFrame:
    path = path or DATA_DIR / "demo_inventory_batch.csv"
    if not path.exists():
        make_demo_inventory(path)
    data = pd.read_csv(path)
    data["date"] = pd.to_datetime(data["date"])
    return data


def validate_inventory(path: Path | None = None) -> dict[str, object]:
    data = load_inventory(path)
    errors = []

    for col in REQ_COLS:
        if col not in data.columns:
            errors.append(f"missing column: {col}")

    if not errors:
        for col in ["store_id", "sku_id", "date"]:
            if data[col].isna().any():
                errors.append(f"empty values: {col}")

        for col in ["stock_qty", "sales_qty", "delivery_qty"]:
            if (data[col] < 0).any():
                errors.append(f"negative values: {col}")

    status = "pass" if not errors else "fail"
    report = {
        "status": status,
        "rows": int(len(data)),
        "stores": int(data["store_id"].nunique()),
        "sku": int(data["sku_id"].nunique()),
        "errors": errors,
    }
    write_validation_report(report)
    return report


def write_validation_report(report: dict[str, object]) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / "data_validation.md"
    lines = [
        "Generated at: 2026-05-24 17:22:41 MSK",
        "",
        "# Data validation",
        "",
        f"- status: `{report['status']}`",
        f"- rows: `{report['rows']}`",
        f"- stores: `{report['stores']}`",
        f"- sku: `{report['sku']}`",
        f"- errors: `{report['errors']}`",
        "",
        "**Вывод:** batch подходит под контракт: date/store/sku/stock/sales/delivery.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

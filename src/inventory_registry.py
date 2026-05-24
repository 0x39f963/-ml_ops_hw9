from __future__ import annotations

import json
from pathlib import Path

from src.inventory_data import REPORTS_DIR


def register_model() -> dict[str, str]:
    train = json.loads((REPORTS_DIR / "train_run.json").read_text(encoding="utf-8"))
    metrics = json.loads((REPORTS_DIR / "model_metrics.json").read_text(encoding="utf-8"))
    row = {
        "model_name": "inventory_stock_model",
        "model_version": "v1",
        "stage": "production_candidate",
        "run_id": train["run_id"],
        "metric": f"mape={metrics['new_mape']:.3f}",
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "local_registry.json").write_text(json.dumps(row, indent=2), encoding="utf-8")

    lines = [
        "# Registry log",
        "",
        "- action: `register_model`",
        f"- model_version: `{row['model_version']}`",
        f"- run_id: `{row['run_id']}`",
        f"- metric: `{row['metric']}`",
        "",
        "**Вывод:** registry хранит факт обучения / метрику / версию модели.",
        "",
    ]
    (REPORTS_DIR / "airflow_registry_log.md").write_text("\n".join(lines), encoding="utf-8")
    return row


def skip_deploy(reason: str = "metric gate failed") -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / "skip_deploy.md"
    path.write_text(
        "\n".join(
            [
                "# Skip deploy",
                "",
                f"- reason: `{reason}`",
                "- active model: previous production version",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path

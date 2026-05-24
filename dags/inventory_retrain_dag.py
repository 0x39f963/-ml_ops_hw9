from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

try:
    from airflow import DAG
    from airflow.operators.empty import EmptyOperator
    from airflow.operators.python import BranchPythonOperator, PythonOperator
    from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
    from airflow.sensors.filesystem import FileSensor
except ImportError:
    class DAG:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class _Task:
        def __init__(self, *args, **kwargs):
            self.task_id = kwargs.get("task_id", args[0] if args else self.__class__.__name__)

        def __rshift__(self, other):
            return other

    class EmptyOperator(_Task):
        pass

    class PythonOperator(_Task):
        pass

    class BranchPythonOperator(_Task):
        pass

    class FileSensor(_Task):
        pass

    class S3KeySensor(_Task):
        pass

from src.inventory_data import DATA_DIR, make_demo_inventory, validate_inventory
from src.inventory_evaluate import compare_with_baseline, evaluate_model
from src.inventory_registry import register_model, skip_deploy
from src.inventory_train import train_model


ROOT = Path(__file__).resolve().parents[1]
BATCH_PATH = DATA_DIR / "demo_inventory_batch.csv"
USE_S3_SENSOR = os.getenv("DZ9_USE_S3_SENSOR", "0") == "1"


def load_inventory_data() -> str:
    if not BATCH_PATH.exists():
        make_demo_inventory(BATCH_PATH)
    return str(BATCH_PATH)


def validate_inventory_data() -> dict[str, object]:
    return validate_inventory(BATCH_PATH)


def train_inventory_model() -> dict[str, object]:
    return train_model(BATCH_PATH)


def evaluate_inventory_model() -> dict[str, float]:
    return evaluate_model()


def choose_model_branch() -> str:
    return compare_with_baseline()


def keep_old_model() -> str:
    skip_deploy("new model is worse than baseline")
    return "old model kept"


default_args = {
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
}


with DAG(
    dag_id="inventory_retrain_pipeline",
    start_date=datetime(2026, 5, 1),
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    tags=["dz9", "inventory", "continuous-training"],
) as dag:
    if USE_S3_SENSOR:
        wait_for_inventory_batch = S3KeySensor(
            task_id="wait_for_inventory_batch",
            bucket_key="incoming/{{ ds }}/inventory.csv",
            bucket_name="inventory-batches",
            aws_conn_id="aws_default",
            poke_interval=60,
            timeout=3600,
            mode="poke",
        )
    else:
        wait_for_inventory_batch = FileSensor(
            task_id="wait_for_inventory_batch",
            filepath=str(BATCH_PATH),
            poke_interval=30,
            timeout=3600,
            mode="poke",
        )

    load = PythonOperator(task_id="load_inventory_data", python_callable=load_inventory_data)
    validate = PythonOperator(task_id="validate_inventory_data", python_callable=validate_inventory_data)
    train = PythonOperator(task_id="train_model", python_callable=train_inventory_model)
    evaluate = PythonOperator(task_id="evaluate_model", python_callable=evaluate_inventory_model)
    compare = BranchPythonOperator(task_id="compare_with_baseline", python_callable=choose_model_branch)
    register = PythonOperator(task_id="register_model", python_callable=register_model)
    skip = PythonOperator(task_id="skip_deploy", python_callable=keep_old_model)
    finish = EmptyOperator(task_id="finish")

    wait_for_inventory_batch >> load
    load >> validate >> train >> evaluate >> compare
    compare >> register >> finish
    compare >> skip >> finish

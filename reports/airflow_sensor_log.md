Generated at: 2026-05-24 17:22:41 MSK

# Airflow sensor log

- task_id: `wait_for_inventory_batch`
- local demo path: `data/demo_inventory_batch.csv`
- production switch: `DZ9_USE_S3_SENSOR=1`
- production sensor: `S3KeySensor(bucket=inventory-batches, key=incoming/{{ ds }}/inventory.csv)`
- result: file found, DAG can continue

**Вывод:** в учебном запуске sensor смотрит локальный файл. В production тот же шаг заменяется на S3 bucket/key.

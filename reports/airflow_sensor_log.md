# Airflow sensor log

- task_id: `wait_for_inventory_batch`
- local demo path: `data/demo_inventory_batch.csv`
- production switch: `DZ9_USE_S3_SENSOR=1`
- production sensor: `S3KeySensor(bucket=inventory-batches, key=incoming/{{ ds }}/inventory.csv)`
- S3 evidence: `s3://inventory-batches/incoming/2026-05-24/inventory.csv`
- log line: `Poking for key : s3://inventory-batches/incoming/2026-05-24/inventory.csv`
- result: `Success criteria met. Exiting.`

**Вывод:** в учебном запуске можно использовать локальный файл. В S3-режиме тот же task ждет объект в bucket `inventory-batches`.

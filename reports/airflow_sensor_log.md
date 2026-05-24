# Airflow sensor log

- task_id: `wait_for_inventory_batch`
- local demo path: `data/demo_inventory_batch.csv`
- active training path: `data/current_inventory_batch.csv`
- S3 switch: `DZ9_USE_S3_SENSOR=1`
- S3 sensor: `S3KeySensor(bucket=inventory-batches, key=incoming/{{ ds }}/inventory.csv)`
- S3 load: `S3Hook.get_key(...).download_file(data/current_inventory_batch.csv)`
- result: sensor нашел файл, load task скопировал/скачал batch в рабочий путь

**Вывод:** sensor не просто отмечает наличие файла. Этот же batch становится входом для validation/train.

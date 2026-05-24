# Airflow task logs

| task | result |
|---|---|
| wait_for_inventory_batch | success |
| load_inventory_data | success, source -> `data/current_inventory_batch.csv` |
| validate_inventory_data | success, при критичной ошибке train не стартует |
| train_model | success |
| evaluate_model | success |
| compare_with_baseline | register_model |
| register_model | success |
| finish | success with `none_failed_min_one_success` |

**Вывод:** порядок задач совпадает с CT loop: wait -> load active batch -> validate gate -> train -> evaluate -> compare -> register/skip.

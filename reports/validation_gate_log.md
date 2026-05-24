# Validation gate log

- task_id: `validate_inventory_data`
- input: `data/current_inventory_batch.csv`
- checks: required columns / empty ids / negative quantities
- fail policy: `raise ValueError(...)`
- downstream effect: `train_model` is not started when validation fails

**Вывод:** data validation теперь не просто пишет отчет, а реально блокирует обучение плохого batch.

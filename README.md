Generated at: 2026-05-24 17:22:41 MSK

# DZ-9. Проектирование ML-системы для расчета складских запасов

Что сделано:

- финальный ноутбук: `HW9_Design_НовиковИван.ipynb`
- Airflow DAG: `dags/inventory_retrain_dag.py`
- код модели: `src/`
- synthetic data: `data/`
- Terraform: `infra/`
- evidence: `reports/`
- MDD/ADR: `adr/0001-latency-mdd-decision.md`
- CI/CD checks: `.github/workflows/dz9-checks.yml`

## Архитектура

Выбран вариант:

```text
batch retraining + reactive trigger через S3/File sensor + metric gate + registry
```

Почему так:

- складские данные обычно приходят batch-ами
- задержка в минуты/часы норм
- Airflow управляет CT loop
- CI/CD проверяет код / Terraform / DAG, но не обучает модель каждый день
- новая модель идет в registry только после compare с baseline

## Запуск evidence локально

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/python scripts/generate_demo_artifacts.py
python3 -m compileall -q src dags scripts
```

## Airflow

Локальный compose:

```bash
docker compose up -d
```

UI:

```text
http://localhost:8080
login: admin
password: admin
```

В DAG есть два tracking-слоя:

- `wait_for_inventory_batch` - локальный FileSensor для учебного запуска
- `DZ9_USE_S3_SENSOR=1` - тот же task использует `S3KeySensor` для production S3/Object Storage

Evidence:

- `reports/airflow_graph.png`
- `reports/airflow_successful_run.png`
- `reports/airflow_sensor_log.md`
- `reports/airflow_compare_log.md`
- `reports/airflow_registry_log.md`

## Terraform

```bash
cd infra
terraform fmt -check
terraform init
terraform validate
terraform plan -out=tfplan
terraform show -no-color tfplan > ../reports/terraform_plan.txt
terraform plan -destroy -out=tfdestroy
terraform show -no-color tfdestroy > ../reports/terraform_destroy_plan.txt
```

На этой машине Terraform не установлен, поэтому в `reports/` сохранен fallback-лог с точными командами и смыслом planned resources.

## MDD

Метрика: latency прогноза запасов.

Файлы:

- `data/reference_latency.csv`
- `data/new_latency.csv`
- `reports/mdd_latency_distribution.png`
- `reports/mdd_test_result.md`
- `adr/0001-latency-mdd-decision.md`

**Итого:**

- latency выросла статистически значимо
- решение в ADR: добавить cache перед чтением истории остатков
- дополнительно переносим тяжелые lag features в batch preprocessing

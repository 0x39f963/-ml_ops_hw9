from __future__ import annotations

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "HW9_Design_НовиковИван.ipynb"


def md(text: str):
    return nbf.v4.new_markdown_cell(text.strip() + "\n")


def code(text: str):
    return nbf.v4.new_code_cell(text.strip() + "\n")


cells = [
    md(
        """
# Домашнее задание 9. Проектирование ML-системы для расчета складских запасов

Generated at: 2026-05-24 17:22:41 MSK

**Коротко:** делаю batch + reactive retraining pipeline.

Airflow отвечает за ML-процесс. CI/CD проверяет код и Terraform. ADR фиксирует MDD-решение.
"""
    ),
    md(
        """
## Карта решения

- `dags/inventory_retrain_dag.py` - Airflow DAG
- `src/` - код загрузки / обучения / оценки / registry
- `infra/` - Terraform
- `reports/` - evidence
- `adr/0001-latency-mdd-decision.md` - MDD решение
- `data/` - synthetic datasets
- `.github/workflows/dz9-checks.yml` - CI/CD checks
"""
    ),
    md(
        """
## 1. Сравнение архитектур ML-конвейеров

| Архитектура | Когда подходит | Плюсы | Минусы | Подходит для запасов |
|---|---|---|---|---|
| Batch retraining | данные приходят пачками раз в день / час | просто / надежно / легко проверять | не мгновенная реакция | да |
| Reactive retraining | обучение стартует при появлении batch-файла или алерта | реагирует на новые данные | нужен sensor / контроль дублей | да |
| Online learning | модель обновляется почти на каждом событии | быстро адаптируется | сложнее rollback / quality gate | нет для учебного минимума |
| Streaming pipeline | данные идут постоянным потоком | near real-time | Kafka/Flink/Spark усложняют систему | только если нужны секунды |
| Human-in-the-loop approval | человек подтверждает выкладку | меньше риск плохого auto-deploy | медленнее обновление | да как safety gate |

**Вывод:**

- выбираю batch + reactive retraining через S3/File sensor
- складские выгрузки обычно приходят пачками
- задержка в минуты/часы норм
- Airflow умеет schedule / sensor / retry / branch
- CI/CD не должен быть ежедневным scheduler для обучения
"""
    ),
    md(
        """
## 2. Airflow DAG

Схема DAG:

```text
wait_for_inventory_batch (FileSensor locally / S3KeySensor in production)
  -> load_inventory_data
  -> validate_inventory_data
  -> train_model
  -> evaluate_model
  -> compare_with_baseline
  -> register_model / skip_deploy
```

В production вместо локального файла используется тот же task `wait_for_inventory_batch`, но с `DZ9_USE_S3_SENSOR=1`:

```text
bucket = inventory-batches
key = incoming/{{ ds }}/inventory.csv
```
"""
    ),
    code(
        """
from pathlib import Path

dag_code = Path("dags/inventory_retrain_dag.py").read_text(encoding="utf-8")
print(dag_code[:3500])
"""
    ),
    md(
        """
## Evidence Airflow

- Graph View: `reports/airflow_graph.png`
- Successful run: `reports/airflow_successful_run.png`
- Sensor log: `reports/airflow_sensor_log.md`
- Compare log: `reports/airflow_compare_log.md`
- Registry log: `reports/airflow_registry_log.md`

![Airflow graph](reports/airflow_graph.png)

**Вывод:**

- DAG содержит sensor / validation / train / evaluate / branch
- плохая модель не регистрируется автоматически
- S3 tracking показан в DAG через переключатель `DZ9_USE_S3_SENSOR=1`
"""
    ),
    md(
        """
## 3. Модель и metric gate

Модель простая, т.к. тут главное не качество прогноза, а MLOps-контур:

- `LinearRegression`
- target: `stock_qty_next_day`
- features: `store_id`, `sku_id`, `stock_qty`, `sales_qty`, `delivery_qty`, `day_of_week`
- baseline: `stock_qty - sales_qty + delivery_qty`
- gate: `new_mape <= 15` и `new_mape <= baseline_mape`
"""
    ),
    code(
        """
from pathlib import Path

print(Path("reports/data_validation.md").read_text(encoding="utf-8"))
print(Path("reports/model_metrics.md").read_text(encoding="utf-8"))
print(Path("reports/airflow_compare_log.md").read_text(encoding="utf-8"))
"""
    ),
    md(
        """
## 4. IaC / Terraform

Минимальная infrastructure-as-code часть:

- storage для batch-файлов
- artifact storage для моделей / метрик
- Airflow config manifest
- MLflow/local registry path

В учебной сдаче это local provider. В production меняется provider, но структура остается.
"""
    ),
    code(
        """
from pathlib import Path

print(Path("infra/main.tf").read_text(encoding="utf-8"))
print("\\n--- terraform plan evidence ---")
print(Path("reports/terraform_plan.txt").read_text(encoding="utf-8")[:1800])
print("\\n--- terraform destroy evidence ---")
print(Path("reports/terraform_destroy_plan.txt").read_text(encoding="utf-8")[:1200])
"""
    ),
    md(
        """
## 5. SLI/SLO и риски

| Уровень | SLI | Источник | Normal/SLO | Warning | Critical | Действие |
|---|---|---|---|---|---|---|
| Бизнес | доля SKU с прогнозом на завтра | output prediction batch | `>= 95%` SKU ежедневно | `90-95%` | `< 90%` | перезапуск DAG / ручной расчет top-SKU |
| Бизнес | доля дефицитных SKU, найденных системой | stockout labels | `>= 80%` за неделю | `65-80%` | `< 65%` | проверить продажи / пересмотреть модель |
| Модель/данные | MAPE прогноза остатков | validation report | `<= 15%` | `15-25%` | `> 25%` | не регистрировать модель / оставить baseline |
| Модель/данные | data validation pass rate | validation task | `100%` critical checks | один warning | любой critical fail | остановить train / incident по данным |
| Код/API | p95 latency прогноза | service logs / synthetic probe | `< 300 ms` за день | `300-1000 ms` | `> 1000 ms` | bottleneck analysis / rollback версии |
| Инфраструктура | successful DAG run rate | Airflow metadata | `>= 99%` daily runs за месяц | 1 падение | 2 падения подряд | разобрать логи / storage / registry |
| Инфраструктура | storage availability | S3/MinIO health | `>= 99.5%` за месяц | retry | нет доступа к batch | не запускать training / incident |

**Риски:**

| risk | уровень | как детектим | что делаем |
|---|---|---|---|
| новый batch не пришел | infra/data | sensor timeout | skip training + уведомление |
| batch с плохой схемой | data/code | validation fail | stop DAG до train |
| модель хуже baseline | model | compare task | `skip_deploy` |
| latency выросла | code/infra | MDD / monitoring | cache / optimize / rollback |
| Terraform удаляет лишнее | infra | review `plan` | approval до apply |
"""
    ),
    md(
        """
## 6. MDD: latency decision

Метрика: `latency_ms` для прогноза запасов.

Гипотезы:

- H0: latency не выросла статистически значимо
- H1: latency выросла статистически значимо
- alpha = 0.05
- test = Mann-Whitney U (без спора про нормальность)
"""
    ),
    code(
        """
from pathlib import Path

import pandas as pd
from scipy.stats import mannwhitneyu

ref = pd.read_csv("data/reference_latency.csv")["latency_ms"]
new = pd.read_csv("data/new_latency.csv")["latency_ms"]

stat, p_value = mannwhitneyu(new, ref, alternative="greater")
print({"stat": round(stat, 3), "p_value": round(p_value, 8)})
print("reference_median", round(ref.median(), 2))
print("new_median", round(new.median(), 2))
print(Path("reports/mdd_test_result.md").read_text(encoding="utf-8"))
"""
    ),
    md(
        """
![MDD latency distribution](reports/mdd_latency_distribution.png)

ADR: `adr/0001-latency-mdd-decision.md`

**Вывод:**

- p-value ниже 0.05
- latency выросла статистически значимо
- решение: добавить cache перед чтением истории остатков
- тяжелые lag features переносим в batch preprocessing
"""
    ),
    code(
        """
from pathlib import Path

print(Path("adr/0001-latency-mdd-decision.md").read_text(encoding="utf-8"))
"""
    ),
    md(
        """
## 7. Итоговый вывод

**Итого:**

- для склада выбрал batch + reactive retraining, т.к. остатки приходят пачками
- Airflow ждет новый batch и запускает ML-процесс
- CI/CD и Airflow разделены: CI проверяет код / DAG / Terraform, Airflow запускает long-running training
- новая модель проходит validation + compare с baseline
- если метрика хуже порога, остается старая модель
- Terraform нужен не для красоты, а чтобы storage / registry / deps были описаны кодом
- MDD сделал по latency: два распределения -> H0/H1 -> p-value -> ADR

**Checklist:**

- [x] архитектуры сравнены
- [x] Airflow DAG с S3/file sensor есть
- [x] Terraform plan/destroy evidence есть
- [x] SLI/SLO на 3 уровнях есть
- [x] MDD + ADR есть
"""
    ),
]

nb = nbf.v4.new_notebook()
nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "pygments_lexer": "ipython3"},
}
NOTEBOOK.write_text(nbf.writes(nb), encoding="utf-8")

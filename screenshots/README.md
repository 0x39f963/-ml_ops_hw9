Generated at: 2026-05-24 19:29:35 MSK

# Скриншоты

Это карта скриншотов для ДЗ-9.

Основной смысл:

- показать, что Airflow DAG реально есть и запускается
- показать S3-like storage через MinIO
- показать metric gate и registry decision
- показать Terraform plan
- показать MDD: latency plot + p-value

Главные скрины для сдачи:

| скрин | зачем |
|---|---|
| [11.png](11.png) | MinIO bucket + входной batch |
| [15.png](15.png) | compare task + `register_model` |
| [16.png](16.png) | структура DAG в CLI |
| [19.png](19.png) | успешный DAG run в Airflow UI |
| [21.png](21.png) | Terraform plan |
| [22.png](22.png) | схема Airflow pipeline |
| [23.png](23.png) | MDD latency distribution |

## 1. Подготовка окружения

![установка зависимостей](1.png)

`1.png` - установка Python-зависимостей в `.venv`.

Evidence слабый, но полезен как старт: видно, что окружение собрано.

![зависимости поставлены](2.png)

`2.png` - зависимости установлены, проект готов к запуску локальных проверок.

`1.png` и `2.png` частично дублируются, поэтому в основной README их не вывожу.

![артефакты reports](3.png)

`3.png` - запуск генерации demo artifacts и список файлов в `reports/`.

Тут видно, что на диске есть Airflow logs / model metrics / MDD result / Terraform evidence.

## 2. Docker Compose / MinIO / Airflow

![первый запуск compose](4.png)

`4.png` - первый запуск compose и перенос портов на `18080`, `19000`, `19001`.

На скрине есть промежуточная ошибка по bucket. Финальное S3 evidence ниже: `9.png`, `11.png`, `18.png`.

![MinIO login](5.png)

`5.png` - MinIO Console открывается на `http://localhost:19001`.

![пустой Object Browser](6.png)

`6.png` - промежуточный вход в Object Browser до успешной загрузки batch-файла.

Как доказательство S3 этот скрин слабый, поэтому основной считаю `11.png` и `18.png`.

![compose запущен](7.png)

`7.png` - Airflow + MinIO подняты через Docker Compose.

![DAG в Airflow](8.png)

`8.png` - в Airflow UI появился DAG `inventory_retrain_pipeline`.

Тут видно, что DAG зарегистрирован и доступен в интерфейсе.

![MinIO init logs](9.png)

`9.png` - init-контейнер создал bucket `inventory-batches` и загрузил `demo_inventory_batch.csv` в ключ `incoming/2026-05-24/inventory.csv`.

Это хороший CLI evidence для S3-like storage.

![Airflow logs](10.png)

`10.png` - diagnostic screen с логами Airflow webserver.

Он показывает, что UI отвечает, но для сдачи слабее чем task logs / Graph View.

![batch в MinIO](11.png)

`11.png` - MinIO Object Browser: bucket `inventory-batches`, путь `incoming/2026-05-24`, файл `inventory.csv`.

Это основной скрин для S3 tracking.

![успешный DAG run list](12.png)

`12.png` - Airflow List Dag Run: DAG `inventory_retrain_pipeline` завершился со state `success`.

## 3. Airflow DAG / metric gate

![Airflow details](13.png)

`13.png` - Airflow Details: один успешный DAG run, `register_model` зеленый, `skip_deploy` пропущен.

Это показывает, что выбрана ветка регистрации модели.

![начало DAG test](14.png)

`14.png` - `airflow dags test`: sensor дождался batch-файл, дальше пошла загрузка данных.

На этом скрине режим локальный (`FileSensor`), поэтому для S3-части нужны `11.png` / `18.png` + sensor log.

![register model log](15.png)

`15.png` - продолжение `airflow dags test`: compare прошел, `register_model` вернул `inventory_stock_model`, `v1`, `production_candidate`.

Это сильный скрин для metric gate и registry.

![DAG tree CLI](16.png)

`16.png` - CLI показывает структуру DAG:

```text
wait -> load -> validate -> train -> evaluate -> compare -> register/skip -> finish
```

![S3 mode compose](17.png)

`17.png` - запуск с `DZ9_USE_S3_SENSOR=1`, т.е. S3 mode через MinIO.

Airflow и MinIO подняты на портах `18080`, `19000`, `19001`.

![MinIO object](18.png)

`18.png` - объект `inventory.csv` лежит в bucket `inventory-batches`.

Это второй сильный скрин для входного batch-файла.

![Airflow graph run](19.png)

`19.png` - Airflow UI: весь pipeline прошел успешно.

Видно tasks: `wait_for_inventory_batch`, `load_inventory_data`, `validate_inventory_data`, `train_model`, `evaluate_model`, `compare_with_baseline`, `register_model`.

## 4. Terraform / IaC

![terraform init validate](20.png)

`20.png` - Terraform запускается через Docker, проходит `init` и `validate`.

![terraform plan](21.png)

`21.png` - `terraform plan`: создаются local manifests для Airflow / MLflow-like registry / storage.

Тут видно:

- `dag_id=inventory_retrain_pipeline`
- `sensor=S3KeySensor_or_local_FileSensor`
- `bucket=inventory-batches`
- `path=incoming/YYYY-MM-DD/inventory.csv`

## 5. Архитектура DAG

![DAG scheme](22.png)

`22.png` - схема Airflow pipeline.

Логика:

```text
sensor -> load -> validate -> train -> evaluate -> compare -> register/skip
```

Хороший поясняющий скрин. Он не заменяет Airflow UI, но помогает быстро понять DAG.

## 6. MDD

![MDD latency plot](23.png)

`23.png` - MDD по latency:

- reference latency около 120 ms
- new latency около 180 ms
- Mann-Whitney U test
- p-value ниже 0.05

Результат в файле: [../reports/mdd_test_result.md](../reports/mdd_test_result.md)

ADR: [../adr/0001-latency-mdd-decision.md](../adr/0001-latency-mdd-decision.md)

**Вывод:**

- latency выросла статистически значимо
- решение: добавить cache перед чтением истории остатков
- тяжелые lag features перенести в batch preprocessing

## 7. Что не считаю главным evidence

- `1.png`, `2.png` - подготовка окружения, можно смотреть как старт
- `4.png`, `6.png` - промежуточные попытки до финальной загрузки batch
- `10.png` - webserver logs, полезно для диагностики, но не для критериев

Для проверки критериев лучше смотреть:

- Airflow: `15.png`, `16.png`, `19.png`
- S3/MinIO: `9.png`, `11.png`, `18.png`
- Terraform: `20.png`, `21.png`
- MDD: `23.png`

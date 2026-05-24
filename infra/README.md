# DZ-9 Terraform

Это учебная IaC-часть для ML-системы запасов.

Что описано:

- storage для batch-файлов (`inventory-batches`)
- artifact storage для моделей / метрик
- manifest для Airflow DAG
- local registry/MLflow-like путь

В этом ДЗ public cloud не поднимаю. Terraform показывает декларативную схему и путь удаления. В production provider меняется на AWS/Yandex/GCP, а структура остается такой же.

## Проверка

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

## Удаление

```bash
cd infra
terraform destroy
```

**Вывод:**

- инфраструктура не считается вечной
- перед apply/destroy надо смотреть plan
- `terraform.tfstate` и `.terraform/` не идут в сдачу

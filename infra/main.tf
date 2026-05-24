locals {
  base_path = "${var.artifact_root}/${var.environment}"
}

resource "local_file" "storage_manifest" {
  filename = "${local.base_path}/storage_manifest.txt"
  content  = "bucket=${var.inventory_bucket_name}\npath=incoming/YYYY-MM-DD/inventory.csv\n"
}

resource "local_file" "mlflow_manifest" {
  filename = "${local.base_path}/mlflow_manifest.txt"
  content  = "tracking_uri=file:../mlruns\nartifact_store=../models\n"
}

resource "local_file" "airflow_manifest" {
  filename = "${local.base_path}/airflow_manifest.txt"
  content  = "dag_id=inventory_retrain_pipeline\nsensor=S3KeySensor_or_local_FileSensor\n"
}

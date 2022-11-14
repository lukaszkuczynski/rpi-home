from airflow import DAG
import datetime
from airflow.contrib.operators.bigquery_get_data import BigQueryGetDataOperator
from airflow.operators.empty import EmptyOperator


DAG_NAME = "google_cloud_cost"
DATASET = "america_health_rankings"
TABLE = "ahr"


with DAG(
    dag_id=DAG_NAME,
    default_args={"retries": 0},
    start_date=datetime.datetime(2022, 1, 1),
    schedule="@daily",
    tags=["finops"],
    catchup=False,
) as dag:
    get_data = BigQueryGetDataOperator(
        task_id="get_data",
        dataset_id=DATASET,
        table_id=TABLE,
        max_results=10,
        selected_fields="edition,state_name",
    )

    end = EmptyOperator(
        task_id="end",
    )

    get_data >> end

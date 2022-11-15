from airflow import DAG
import datetime
from airflow.contrib.operators.bigquery_get_data import BigQueryGetDataOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from airflow.models import Variable
from airflow.hooks.postgres_hook import PostgresHook
from airflow.operators.python import PythonOperator

DAG_NAME = "google_cloud_cost"
DATASET = "america_health_rankings"
TABLE = "ahr"


def curr_date_str_filename():
    return f"{datetime.datetime.now().strftime('%Y%m%d')}.csv"


def get_google_cloud_costs(**kwargs):
    hook = BigQueryHook(location="europe-central2")
    pg_hook = PostgresHook(postgres_conn_id="postgres_client")
    execution_date = kwargs["execution_date"]
    start_date_str = execution_date.replace(day=1).strftime("%Y-%m-%d")
    end_date_str = execution_date.strftime("%Y-%m-%d")
    sql_query = "SELECT * FROM datasettest.tab LIMIT 1000;"
    records = hook.get_records(sql_query)
    print(records)


with DAG(
    dag_id=DAG_NAME,
    default_args={"retries": 0},
    start_date=datetime.datetime(2022, 1, 1),
    schedule="@daily",
    tags=["finops"],
    catchup=False,
) as dag:

    get_data = PythonOperator(
        python_callable=get_google_cloud_costs,
        task_id="get_costs",
        provide_context=True,
    )

    end = EmptyOperator(
        task_id="end",
    )

    get_data >> end

# apply leastprivilege for this user https://cloud.google.com/bigquery/docs/exporting-data

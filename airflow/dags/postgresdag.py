import datetime

from airflow import DAG
from airflow.example_dags.subdags.subdag import subdag
from airflow.operators.empty import EmptyOperator
from airflow.operators.subdag import SubDagOperator
from airflow.hooks.postgres_hook import PostgresHook

from airflow.providers.amazon.aws.hooks.base_aws import AwsBaseHook
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow import DAG
import datetime

from airflow.providers.postgres.operators.postgres import PostgresOperator

DAG_NAME = "postgres_sample_dag"


def read_postgres():
    hook = PostgresHook(postgres_conn_id="postgres_client")
    print(dir(hook))
    ce_client = hook.test_connection()


with DAG(
    dag_id=DAG_NAME,
    default_args={"retries": 0},
    start_date=datetime.datetime(2022, 1, 1),
    schedule="@once",
    tags=["example"],
) as dag:

    postgres_hook_test = PythonOperator(
        python_callable=read_postgres,
        task_id="read_postgres",
    )

    postgres_operator_test = PostgresOperator(
        postgres_conn_id="postgres_client",
        task_id="dosth_with_postgresoperator",
        sql="""
            select * from
            raw_data
          """,
    )

    end = EmptyOperator(
        task_id="end",
    )

    postgres_hook_test >> postgres_operator_test >> end

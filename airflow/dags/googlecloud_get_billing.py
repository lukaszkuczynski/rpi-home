from airflow import DAG
import datetime
from airflow.operators.empty import EmptyOperator
from airflow.models import Variable
from airflow.hooks.postgres_hook import PostgresHook
from airflow.operators.python import PythonOperator
import requests
import json

SOURCE_SYSTEM_IDENTIFIER = 'gcloud'
DAG_NAME = 'gcloud_cost_reader_dag'

def curr_date_str_filename():
    return f"{datetime.datetime.now().strftime('%Y%m%d')}.csv"


def get_last_file(**kwargs):
    root_url = Variable.get("FILESERVER_URL")
    listing_url = root_url
    resp = requests.get(listing_url)
    print(f"File listing : {resp.content}")
    # to replace with currdate and path..
    filepath = "folder1/000000000000.json"
    file_url = f"{root_url}?filename={filepath}"
    file_resp = requests.get(file_url)
    raw_content = file_resp.text
    print("received content...")
    print(raw_content)
    rows = raw_content.split('\n')
    elements = [json.loads(row) for row in rows if len(row)>0 ]
    pg_hook = PostgresHook(postgres_conn_id="postgres_client")
    pg_conn = pg_hook.get_conn()
    cursor = pg_conn.cursor()
    cursor.execute(
        f"""
            INSERT INTO raw_data(raw_data, source_system)
            VALUES('{json.dumps(elements)}','{SOURCE_SYSTEM_IDENTIFIER}')
        """
    )
    pg_conn.commit()
    


with DAG(
    dag_id=DAG_NAME,
    default_args={"retries": 0},
    start_date=datetime.datetime(2022, 1, 1),
    schedule="@daily",
    tags=["finops"],
    catchup=False,
) as dag:

    download_todays_export = PythonOperator(
        python_callable=get_last_file,
        task_id="get_last_file",
        provide_context=True,
    )

    # get_data = PythonOperator(
    #     python_callable=get_google_cloud_costs,
    #     task_id="get_costs",
    #     provide_context=True,
    # )

    end = EmptyOperator(
        task_id="end",
    )

    download_todays_export >> end

# apply leastprivilege for this user https://cloud.google.com/bigquery/docs/exporting-data

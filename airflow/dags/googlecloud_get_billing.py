from airflow import DAG
import datetime
from airflow.operators.empty import EmptyOperator
from airflow.models import Variable
from airflow.hooks.postgres_hook import PostgresHook
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
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
    execution_date = kwargs["execution_date"]
    filepath = f"folder1/{datetime.datetime.strftime(execution_date-datetime.timedelta(days=1), '%Y%m%d')}000000000000.json"
    print(f"Filepath to be fetched is {filepath}")
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

    move_raw_data_to_conform = PostgresOperator(
        task_id="move_raw_data_to_conform",
        postgres_conn_id="postgres_client",
        sql="""
            with json_rows as (select json_array_elements(raw_data.raw_data) as row
                            from raw_data
                            where source_system = 'gcloud'),
            raw_data_source as (
                select
                    to_timestamp(row ->> 'usage_start_time', 'YYYY-MM-DDXHH24:MI:SS.MS') usage_start_time,
                    to_timestamp(row ->> 'usage_end_time', 'YYYY-MM-DDXHH24:MI:SS.MS') usage_end_time,
                    row->'service'->>'description' as service_description,
                    cast(row->>'cost' as float) as cost,
                    row->'project'->>'id' as project_id,
                    row->'location'->>'region' as region
                from json_rows
            )
            insert into conform_spendings(
                    start_date,
                    end_date,
                    resource_group,
                    amount,
                    tags,
                    source_system,
                    region
                )
            select
                usage_start_time,
                usage_end_time,
                service_description,
                cost,    
                project_id,
                'gcloud',
                region
            from raw_data_source;
          """,
    )

    end = EmptyOperator(
        task_id="end",
    )

    download_todays_export >> move_raw_data_to_conform >> end

# apply leastprivilege for this user https://cloud.google.com/bigquery/docs/exporting-data

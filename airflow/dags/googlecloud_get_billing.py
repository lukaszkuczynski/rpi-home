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
    print(file_resp)
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
    schedule="0 2 * * *",
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
            with json_rows as (
                select 
                    json_array_elements(raw_data.raw_data) as row,
                    updated_at
                from raw_data
                where source_system = 'gcloud'
            ),
            raw_data_source as (
                select
                    to_timestamp(row ->> 'usage_start_time', 'YYYY-MM-DDXHH24:MI:SS.MS') usage_start_time,
                    to_timestamp(row ->> 'usage_end_time', 'YYYY-MM-DDXHH24:MI:SS.MS') usage_end_time,
                    row->'service'->>'description' as service_description,
                    cast(row->>'cost' as float) as cost,
                    row->'project'->>'id' as project_id,
                    row->'location'->>'region' as region,
                    row->'export_time', 
                    updated_at
                from json_rows
            ),
            duplicated_row_candidates as (
                select
                    usage_start_time,
                    usage_end_time,
                    service_description,
                    cost,    
                    project_id,
                    'gcloud' as source_system,
                    region, 
                    updated_at,
                    row_number() over (partition by usage_start_time, service_description, project_id order by updated_at desc) as rowno
                from raw_data_source
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
                cast(usage_start_time as date) start_date,
                cast(usage_end_time as date) end_date,
                service_description,
                sum(cost),
                project_id,
                source_system,
                region
            from duplicated_row_candidates
            where rowno=1
            group by 1,2,3,5,6,7
          """,
    )

    move_to_clean = PostgresOperator(
        task_id="move_to_clean",
        postgres_conn_id="postgres_client",        
        sql = """
            with dedup_conform_spendings as (
                with conform_plus_rowno as (
                    select start_date, end_date, resource_group, amount, source_system, tags, coalesce(region, 'region') as region,
                        row_number() over (partition by start_date, resource_group, source_system, region order by updated_at desc) rowno
                    from conform_spendings
                )
                select *
                from conform_plus_rowno
                where rowno=1
            )
            insert into clean_spendings(start_date, end_date, resource_group, amount, source_system, tags, region)
            select start_date, end_date, resource_group, amount, source_system, tags, region
            from dedup_conform_spendings
            on conflict (start_date, resource_group, source_system, region) do update
            set amount=excluded.amount;
        """
    )

    end = EmptyOperator(
        task_id="end",
    )

    download_todays_export >> move_raw_data_to_conform >> move_to_clean >> end

# apply leastprivilege for this user https://cloud.google.com/bigquery/docs/exporting-data

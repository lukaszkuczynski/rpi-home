from airflow.providers.amazon.aws.hooks.base_aws import AwsBaseHook
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow import DAG
import datetime
import json
from airflow.hooks.postgres_hook import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator

DAG_NAME = "aws_cost_reader_dag_company"
SOURCE_SYSTEM_IDENTIFIER = "aws_second"


def get_aws_costs(**kwargs):
    hook = AwsBaseHook(client_type="ce", aws_conn_id="aws_second")
    pg_hook = PostgresHook(postgres_conn_id="postgres_client")
    ce_client = hook.get_conn()
    execution_date = kwargs["execution_date"]
    start_date_str = execution_date.replace(day=1).strftime("%Y-%m-%d")
    end_date_str = execution_date.strftime("%Y-%m-%d")
    cost_usage = ce_client.get_cost_and_usage(
        TimePeriod={"Start": start_date_str, "End": end_date_str},
        Granularity="DAILY",
        Metrics=["BlendedCost"],
        GroupBy=[
            {"Type": "DIMENSION", "Key": "SERVICE"},
            {"Type": "DIMENSION", "Key": "REGION"},
        ],
    )
    pg_conn = pg_hook.get_conn()
    cursor = pg_conn.cursor()
    cost_usage_str = json.dumps(cost_usage)
    cursor.execute(
        f"""
            INSERT INTO raw_data(raw_data, source_system)
            VALUES('{cost_usage_str}','{SOURCE_SYSTEM_IDENTIFIER}')
        """
    )
    pg_conn.commit()
    print(cost_usage)


with DAG(
    dag_id=DAG_NAME,
    default_args={"retries": 0},
    start_date=datetime.datetime(2022, 1, 1),
    schedule="0 2 * * *",
    tags=["finops"],
    catchup=False,
) as dag:

    get_data = PythonOperator(
        python_callable=get_aws_costs,
        task_id="get_costs",
        provide_context=True,
    )

    move_raw_data_to_conform = PostgresOperator(
        task_id="move_raw_data_to_conform",
        postgres_conn_id="postgres_client",
        sql=f"""
            with raw_data_source as (
                select CAST(
                        json_array_elements(raw_data->'ResultsByTime')->'TimePeriod'->>'Start' AS DATE
                    ) as date_start,
                    CAST(
                        json_array_elements(raw_data->'ResultsByTime')->'TimePeriod'->>'End' AS DATE
                    ) as date_end,
                    json_array_elements(
                        json_array_elements(raw_data->'ResultsByTime')->'Groups'
                    )->'Keys'->>1 as region,
                    json_array_elements(
                        json_array_elements(raw_data->'ResultsByTime')->'Groups'
                    )->'Keys'->>0 as resource_group,
                    CAST(
                        json_array_elements(
                            json_array_elements(raw_data->'ResultsByTime')->'Groups'
                        )->'Metrics'->'BlendedCost'->>'Amount' AS FLOAT
                    ) as amount,
                    '{SOURCE_SYSTEM_IDENTIFIER}' as source_system
                from raw_data
            )
            insert into conform_spendings(
                    start_date,
                    end_date,
                    resource_group,
                    amount,
                    source_system,
                    region
                )
            select date_start,
                date_end,
                resource_group,
                amount,
                source_system,
                region
            from raw_data_source
          """,
    )

    move_to_clean = PostgresOperator(
        task_id="move_to_clean",
        postgres_conn_id="postgres_client",
        sql="""
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
        """,
    )

    end = EmptyOperator(
        task_id="end",
    )

    get_data >> move_raw_data_to_conform >> move_to_clean >> end

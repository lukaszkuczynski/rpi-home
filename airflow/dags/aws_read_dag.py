from airflow.providers.amazon.aws.hooks.base_aws import AwsBaseHook
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow import DAG
import datetime

DAG_NAME = 'aws_sample_dag'


def get_aws_costs():
    hook = AwsBaseHook(client_type='ce')
    ce_client = hook.get_conn()
    cost_usage = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': '2022-10-02',
            'End': '2022-10-23'
        },
        Granularity='DAILY',
        Filter = { 
            "Dimensions": {
                "Key": "REGION", 
                "Values": [ "eu-central-1" ] 
            }
        },
        Metrics = ['BlendedCost'],
        GroupBy = [
            {
                "Type": "DIMENSION",
                "Key":"SERVICE"
            }
        ]
    )
    print(cost_usage)



with DAG(
    dag_id=DAG_NAME,
    default_args={"retries": 0},
    start_date=datetime.datetime(2022, 1, 1),
    schedule="@once",
    tags=['example'],
) as dag:

    get_data = PythonOperator(
        python_callable = get_aws_costs,
        task_id='get_costs'
    )

    end = EmptyOperator(
        task_id='end',
    )

    get_data >> end
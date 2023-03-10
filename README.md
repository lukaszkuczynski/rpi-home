need to define follwing files to run Airflow docker image:

`.db.env` file with Postgres DB credentials
```
POSTGRES_PASSWORD=<pg_password_goes_here>
POSTGRES_DB=<pgdbname>
```

`.secret.env` with connection strings
```
AIRFLOW_CONN_AWS_DEFAULT=aws://user:key
AIRFLOW_CONN_POSTGRES_CLIENT=postgres://user:<pg_password_goes_here>@postgres_client:5432/<pgdbname>
```


todo:
- adjust timestart for airflow for 1 day forward?


 aws ce get-cost-and-usage --time-period '{"Start":"2023-03-08", "End":"2023-03-09"}' --granularity DAILY --metrics BLENDED_COST --group-by '[{"Type": "DIMENSION", "Key": "REGION"},{"Type": "DIMENSION", "Key":"SERVICE"}]'
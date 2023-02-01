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
- aws get region by cli
- create chart from pg, streamlit?
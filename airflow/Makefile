dbclean:
	docker-compose stop postgres_client
	docker-compose rm -f postgres_client  
	docker volume rm airflow_postgres-db-volume-client


build:
	docker build . -t lukrpihome/airflow

runti:
	docker run --privileged --rm -ti lukrpihome/airflow /bin/bash


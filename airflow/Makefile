.PHONY: logs

dbclean:
	docker-compose stop postgres_client
	docker-compose rm -f postgres_client  
	docker volume rm airflow_postgres-db-volume-client


build:
	docker build . -t lukrpihome/airflow

runti:
	docker run -p 8080:8080 --privileged --rm -ti lukrpihome/airflow /bin/bash

up:
	docker-compose -f docker-compose-rpi.yaml up -d

logs:
	docker-compose -f docker-compose-rpi.yaml logs -f

exec:
	docker-compose -f docker-compose-rpi.yaml exec -ti standalone /bin/bash

.PHONY: logs

dbclean:
	docker-compose stop postgres_client
	docker-compose rm -f postgres_client  
	docker volume rm airflow_postgres-db-volume-client


build:
	docker build . -t lukrpihome/airflow

build_arm:
	docker build . -t lukrpihome/airflow_arm64 -f Dockerfile_arm64 

runti:
	docker run -p 8080:8080 --privileged --rm -ti lukrpihome/airflow /bin/bash

up:
	docker-compose  up

down:
	docker-compose  down
	docker-compose  rm -f
logs:
	docker-compose  logs -f

exec:
	docker-compose  exec -ti standalone /bin/bash

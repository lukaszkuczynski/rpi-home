.PHONY: logs

dbclean: down
	docker-compose rm -f postgres  
	docker volume rm airflow_postgres-db-volume
	docker-compose rm -f postgres_client  
	docker volume rm airflow_postgres-db-volume-client

build:
	docker build . -t lukrpihome/airflow:arm7

build_arm64:
	docker build . -t lukrpihome/airflow:arm64 -f Dockerfile_arm64 

runti:
	docker run -p 8080:8080 --privileged --rm -ti lukrpihome/airflow /bin/bash

up:
	docker-compose up -d

down:
	docker-compose down
	docker-compose rm -f

logs:
	docker-compose logs -f

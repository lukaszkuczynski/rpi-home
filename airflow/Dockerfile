FROM python:3.7-slim-buster

RUN apt-get update -yqq \
    	&& apt-get upgrade -yqq \
    	&& apt-get install -yqq --no-install-recommends \
	apt-utils \
	build-essential \
	libffi-dev \
	libpq-dev \
	libssl-dev \
	python3-pandas \
	python3-numpy

ENV PYTHONPATH="${PYTHONPATH}:/usr/lib/python3/dist-packages"


RUN pip install -U pip setuptools wheel
RUN pip install -U pip cryptography==3.1.1 pyOpenSSL==19.1.0

COPY pip.conf sources.list ./
RUN mv ./pip.conf /etc \
    && export PIP_CONFIG_FILE=/etc/pip.conf

RUN pip install -U pip apache-airflow[aws,slack,postgres]

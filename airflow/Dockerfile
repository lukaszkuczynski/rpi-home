FROM arm32v7/python:3.7.15
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN python3 -m pip install cryptography==3.1.1
RUN pip install --no-cache-dir -r requirements.txt

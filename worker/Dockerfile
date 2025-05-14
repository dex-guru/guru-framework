FROM docker-registry.dexguru.biz/dex.guru/utils/python:3.12.6

RUN apt-get update && apt-get install -y git gcc g++ libpq-dev python3-dev
RUN pip install -U pip

ADD requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt

RUN mkdir /code/
WORKDIR /code/
ADD . /code/
ENV PYTHONPATH=.

CMD ["python", "web3_workers/check_transaction_status.py"]

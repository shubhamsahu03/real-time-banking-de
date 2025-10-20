FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir \
    boto3 \
    kafka-python \
    python-dotenv \
    pandas \
    fastparquet \
    pyarrow \
    requests   \
    aiokafka 

CMD ["python", "kafka_to_minio.py"]

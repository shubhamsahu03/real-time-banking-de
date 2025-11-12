# Real-Time Banking Data Engineering Pipeline

## 📋 Project Overview

This project implements a complete end-to-end real-time data engineering pipeline for banking transactions. It captures changes from a PostgreSQL OLTP database using Change Data Capture (CDC), streams them through Apache Kafka, stores them in a data lake (MinIO), and loads them into Snowflake for analytics. The pipeline uses Apache Airflow for orchestration and DBT for data transformation, demonstrating a modern data stack architecture.

## ✨ Core Features

- **Real-Time Change Data Capture**: Captures database changes in real-time using Debezium PostgreSQL connector with logical replication.

- **Event Streaming Pipeline**: Streams banking transactions (customers, accounts, transactions) through Kafka topics to enable real-time processing.

- **Data Lake Storage**: Persists streaming data as Parquet files in MinIO (S3-compatible storage) with date partitioning. 

- **Data Warehouse Integration**: Automated ETL pipeline to load data from MinIO into Snowflake using Apache Airflow.

- **Synthetic Data Generation**: Continuous generation of realistic banking data using Faker library for testing and development.

## 🛠️ Technology Stack

**Languages & Frameworks:**
- Python 3.x
- SQL

**Data Infrastructure:**
- PostgreSQL 15 (with logical replication enabled) 
- Apache Kafka & Zookeeper 
- Debezium Connect  
- MinIO (S3-compatible object storage) 
- Snowflake Data Warehouse
- Apache Airflow 
- DBT (Data Build Tool)

**Python Libraries:**
- `psycopg2` - PostgreSQL adapter
- `kafka-python` - Kafka consumer/producer
- `boto3` - AWS S3/MinIO client
- `pandas` - Data manipulation
- `Faker` - Synthetic data generation
- `snowflake-connector-python` - Snowflake integration

**Containerization:**
- Docker & Docker Compose

## 📋 Prerequisites

Before running this project, ensure you have the following installed:

- **Docker** (version 20.x or higher)
- **Docker Compose** (version 3.8 or higher)
- **Snowflake Account** (for data warehouse integration)
- **Git** (to clone the repository)

## 🚀 Build/Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/shubhamsahu03/real-time-banking-de.git
cd real-time-banking-de
```

### 2. Set Up Environment Variables
Create a `.env` file in the root directory with the following configuration:

```bash
# PostgreSQL Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=banking_db
POSTGRES_USER=banking_user
POSTGRES_PASSWORD=your_secure_password

# Kafka Configuration
KAFKA_BOOTSTRAP=kafka:9092
KAFKA_GROUP=banking_consumer_group

# MinIO Configuration
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=banking-data
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# Snowflake Configuration
SNOWFLAKE_USER=your_snowflake_user
SNOWFLAKE_PASSWORD=your_snowflake_password
SNOWFLAKE_ACCOUNT=your_account.region
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DB=BANKING_DB
SNOWFLAKE_SCHEMA=RAW

# Airflow Configuration
AIRFLOW_DB_USER=airflow
AIRFLOW_DB_PASSWORD=airflow
AIRFLOW_DB_NAME=airflow
```

### 3. Initialize Database Schema
```bash
# Start PostgreSQL container first
docker-compose up -d postgres

# Initialize the banking schema
docker exec -i postgres psql -U banking_user -d banking_db < postgres/schema.sql
```

### 4. Start All Services
```bash
# Start all containers in detached mode
docker-compose up -d

# Verify all services are running
docker-compose ps
```

### 5. Initialize Airflow
```bash
# Initialize Airflow database
docker exec -it airflow-webserver airflow db init

# Create Airflow admin user
docker exec -it airflow-webserver airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin
```

## 📖 Usage / Example Session

### Step 1: Set Up Debezium Connector
The Debezium connector captures changes from PostgreSQL and publishes them to Kafka topics.

```bash
# Run the connector setup script
python kafka-debezium/generate_and_post_connector.py
```

**Expected Output:**
```
2025-01-10 10:30:00 [INFO] 🧩 Connector configuration built successfully:
2025-01-10 10:30:01 [INFO] Attempt 1/5: Creating connector...
2025-01-10 10:30:02 [INFO] ✅ Connector created successfully!
2025-01-10 10:30:02 [INFO] 🚀 Connector setup completed successfully.
```

### Step 2: Generate Banking Data
Start generating synthetic banking transactions:

```bash
# Run in continuous mode (generates data every 2 seconds)
python data-generator/faker_generator.py

# Or run once for testing
python data-generator/faker_generator.py --once
```

**Expected Output:**
```
2025-01-10 10:31:00 [INFO] ✅ Connected to Postgres successfully.
2025-01-10 10:31:01 [INFO] --- Iteration 1 started ---
2025-01-10 10:31:02 [INFO] ✅ Inserted 10 customers, 20 accounts, and 50 transactions.
2025-01-10 10:31:02 [INFO] --- Iteration 1 finished ---
```

### Step 3: Start Kafka Consumer
The consumer reads from Kafka topics and writes to MinIO in Parquet format:

```bash
# Run the Kafka to MinIO consumer
python consumer/kafka_to_minio.py
```

**Expected Output:**
```
✅ Connected to Kafka. Listening for messages...
[banking_server.public.customers] -> {'id': 1, 'first_name': 'John', 'last_name': 'Doe', ...}
[banking_server.public.accounts] -> {'id': 1, 'customer_id': 1, 'account_type': 'CHECKING', ...}
✅ Uploaded 50 records to s3://banking-data/transactions/date=2025-01-10/transactions_103045123456.parquet
```

### Step 4: Access Services

- **Airflow UI**: http://localhost:8080 (admin/admin)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Kafka Connect UI**: http://localhost:8083/connectors

### Step 5: Monitor the Pipeline

Check Airflow DAGs are running:
1. Navigate to Airflow UI at http://localhost:8080
2. Enable the `minio_to_snowflake_banking` DAG
3. Monitor task execution and logs

Verify data in Snowflake:
```sql
-- Connect to your Snowflake account and run:
SELECT COUNT(*) FROM BANKING_DB.RAW.CUSTOMERS;
SELECT COUNT(*) FROM BANKING_DB.RAW.ACCOUNTS;
SELECT COUNT(*) FROM BANKING_DB.RAW.TRANSACTIONS;
```

## 📊 Architecture Overview

The pipeline follows this data flow:

![Architecture Diagram](https://github.com/shubhamsahu03/real-time-banking-de/blob/master/assets/architecture_diagram.png)

## 🗂️ Project Structure

```
real-time-banking-de/
├── banking_dbt/              # DBT project for data transformations
├── consumer/                 # Kafka consumer to MinIO
│   └── kafka_to_minio.py
├── data-generator/           # Synthetic data generator
│   └── faker_generator.py
├── docker/                   # Docker configurations
│   └── dags/                # Airflow DAG definitions
├── kafka-debezium/          # Debezium connector setup
│   └── generate_and_post_connector.py
├── postgres/                # PostgreSQL schema
│   └── schema.sql
└── docker-compose.yml       # Container orchestration
```

## 🔑 Database Schema

The banking system uses three main tables:

- **customers**: Customer information (id, first_name, last_name, email, created_at)
- **accounts**: Bank accounts (id, customer_id, account_type, balance, currency, created_at)
- **transactions**: Financial transactions (id, account_id, txn_type, amount, related_account_id, status, created_at)

## 🛑 Stopping the Pipeline

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clears all data)
docker-compose down -v
```

## 👤 Author

**shubhamsahu03**
- GitHub: [@shubhamsahu03](https://github.com/shubhamsahu03)

---

## 📌 Notes

- The PostgreSQL database is configured with logical replication (`wal_level=logical`) to enable CDC.
- Kafka topics are automatically created by Debezium with the prefix `banking_server`.
- The Airflow DAG runs every minute to sync data from MinIO to Snowflake.
- Data in MinIO is partitioned by date for efficient querying.

## 🐛 Troubleshooting

**Issue**: Debezium connector fails to start
- **Solution**: Ensure PostgreSQL is fully started and accessible. Check that `wal_level=logical` is configured.

**Issue**: Kafka consumer not receiving messages
- **Solution**: Verify Debezium connector is created successfully. Check Kafka topics exist using: `docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092`

**Issue**: Airflow DAG not running
- **Solution**: Check Airflow logs: `docker logs airflow-scheduler`. Ensure all environment variables for Snowflake are correctly set.

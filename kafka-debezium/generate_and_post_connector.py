import os
import json
import requests
import time
import sys
import logging
from dotenv import load_dotenv
from requests.exceptions import ConnectionError, Timeout, RequestException

# -----------------------------
# Logging setup
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

# -----------------------------
# Validate required environment variables
# -----------------------------
required_env_vars = [
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB"
]

missing_vars = [v for v in required_env_vars if not os.getenv(v)]
if missing_vars:
    logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

# -----------------------------
# Build connector JSON in memory
# -----------------------------
connector_config = {
    "name": "postgres-connector",
    "config": {
        "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
        "database.hostname": os.getenv("POSTGRES_HOST"),
        "database.port": os.getenv("POSTGRES_PORT"),
        "database.user": os.getenv("POSTGRES_USER"),
        "database.password": os.getenv("POSTGRES_PASSWORD"),
        "database.dbname": os.getenv("POSTGRES_DB"),
        "topic.prefix": "banking_server",
        "table.include.list": "public.customers,public.accounts,public.transactions",
        "plugin.name": "pgoutput",
        "slot.name": "banking_slot",
        "publication.autocreate.mode": "filtered",
        "tombstones.on.delete": "false",
        "decimal.handling.mode": "double",
    },
}

# Pretty-print for debugging clarity
logger.info("🧩 Connector configuration built successfully:")
logger.info(json.dumps(connector_config, indent=2))

# -----------------------------
# Function: Create connector with retry
# -----------------------------
def create_connector(config, retries=5, delay=3):
    url = "http://localhost:8083/connectors"
    headers = {"Content-Type": "application/json"}

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{retries}: Creating connector...")
            response = requests.post(url, headers=headers, data=json.dumps(config), timeout=10)

            if response.status_code == 201:
                logger.info("✅ Connector created successfully!")
                return True
            elif response.status_code == 409:
                logger.warning("⚠️ Connector already exists.")
                return True
            else:
                logger.error(f"❌ Failed to create connector ({response.status_code}): {response.text}")
                return False

        except (ConnectionError, Timeout) as e:
            logger.warning(f"⚠️ Connect attempt failed ({e}). Retrying in {delay}s...")
            time.sleep(delay)
        except RequestException as e:
            logger.error(f"❌ Unexpected request error: {e}")
            return False

    logger.critical("❌ All connection attempts failed. Could not create connector.")
    return False

# -----------------------------
# Main execution
# -----------------------------
if __name__ == "__main__":
    success = create_connector(connector_config)
    if not success:
        logger.error("❌ Connector setup failed.")
        sys.exit(1)
    else:
        logger.info("🚀 Connector setup completed successfully.")
        sys.exit(0)

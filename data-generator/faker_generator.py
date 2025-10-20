import time
import psycopg2
from psycopg2 import OperationalError, InterfaceError, ProgrammingError
from decimal import Decimal, ROUND_DOWN
from faker import Faker
import random
import argparse
import sys
import os
import logging
from dotenv import load_dotenv

# -----------------------------
# Setup logging
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
# Project configuration (constants)
# -----------------------------
NUM_CUSTOMERS = 10
ACCOUNTS_PER_CUSTOMER = 2
NUM_TRANSACTIONS = 50
MAX_TXN_AMOUNT = 1000.00
CURRENCY = "USD"

INITIAL_BALANCE_MIN = Decimal("10.00")
INITIAL_BALANCE_MAX = Decimal("1000.00")

DEFAULT_LOOP = True
SLEEP_SECONDS = 2

# -----------------------------
# CLI override
# -----------------------------
parser = argparse.ArgumentParser(description="Run fake data generator for banking DB.")
parser.add_argument("--once", action="store_true", help="Run a single iteration and exit")
parser.add_argument("--seed", type=int, help="Optional random seed for deterministic runs")
args = parser.parse_args()

LOOP = not args.once and DEFAULT_LOOP

if args.seed:
    random.seed(args.seed)

# -----------------------------
# Sanity check: required env vars
# -----------------------------
required_env_vars = [
    "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"
]

for var in required_env_vars:
    if not os.getenv(var):
        logger.error(f"Missing required environment variable: {var}")
        sys.exit(1)

# -----------------------------
# Helper: random money generator
# -----------------------------
fake = Faker()

def random_money(min_val: Decimal, max_val: Decimal) -> Decimal:
    val = Decimal(str(random.uniform(float(min_val), float(max_val))))
    return val.quantize(Decimal("0.01"), rounding=ROUND_DOWN)

# -----------------------------
# Database connection
# -----------------------------
def connect_db(retries=5, delay=3):
    """Retry logic for connecting to PostgreSQL."""
    for attempt in range(1, retries + 1):
        try:
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST"),
                port=os.getenv("POSTGRES_PORT"),
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
            )
            conn.autocommit = False
            logger.info("✅ Connected to Postgres successfully.")
            return conn
        except OperationalError as e:
            logger.warning(f"Attempt {attempt}/{retries}: Failed to connect to DB. Retrying in {delay}s... ({e})")
            time.sleep(delay)
    logger.critical("❌ Could not connect to Postgres after multiple retries. Exiting.")
    sys.exit(1)

conn = connect_db()
cur = conn.cursor()

# -----------------------------
# Core generation logic (single iteration)
# -----------------------------
def run_iteration():
    try:
        customers = []
        accounts = []

        # 1. Generate customers
        for _ in range(NUM_CUSTOMERS):
            first_name = fake.first_name()
            last_name = fake.last_name()
            # safer unique email generation
            email = f"{first_name.lower()}.{last_name.lower()}.{random.randint(1000,9999)}@example.com"

            cur.execute(
                """
                INSERT INTO customers (first_name, last_name, email)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (first_name, last_name, email),
            )
            customers.append(cur.fetchone()[0])

        # 2. Generate accounts
        for customer_id in customers:
            for _ in range(ACCOUNTS_PER_CUSTOMER):
                account_type = random.choice(["SAVINGS", "CHECKING"])
                initial_balance = random_money(INITIAL_BALANCE_MIN, INITIAL_BALANCE_MAX)
                cur.execute(
                    """
                    INSERT INTO accounts (customer_id, account_type, balance, currency)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (customer_id, account_type, initial_balance, CURRENCY),
                )
                accounts.append(cur.fetchone()[0])

        # 3. Generate transactions
        txn_types = ["DEPOSIT", "WITHDRAWAL", "TRANSFER"]
        for _ in range(NUM_TRANSACTIONS):
            account_id = random.choice(accounts)
            txn_type = random.choice(txn_types)
            amount = round(random.uniform(1, MAX_TXN_AMOUNT), 2)
            related_account = None
            if txn_type == "TRANSFER" and len(accounts) > 1:
                related_account = random.choice([a for a in accounts if a != account_id])

            cur.execute(
                """
                INSERT INTO transactions (account_id, txn_type, amount, related_account_id, status)
                VALUES (%s, %s, %s, %s, 'COMPLETED')
                """,
                (account_id, txn_type, amount, related_account),
            )

        conn.commit()
        logger.info(f"✅ Inserted {len(customers)} customers, {len(accounts)} accounts, and {NUM_TRANSACTIONS} transactions.")

    except (Exception, ProgrammingError) as e:
        conn.rollback()
        logger.error(f"❌ Error during iteration, rolled back transaction: {e}")

# -----------------------------
# Main execution loop
# -----------------------------
try:
    iteration = 0
    while True:
        iteration += 1
        logger.info(f"\n--- Iteration {iteration} started ---")
        run_iteration()
        logger.info(f"--- Iteration {iteration} finished ---")

        if not LOOP:
            break

        time.sleep(SLEEP_SECONDS)

except KeyboardInterrupt:
    logger.info("🛑 Interrupted by user. Cleaning up and exiting...")

except InterfaceError:
    logger.warning("⚠️ Lost connection to database. Reconnecting...")
    conn = connect_db()
    cur = conn.cursor()

except Exception as e:
    logger.exception(f"Unexpected error: {e}")

finally:
    try:
        cur.close()
        conn.close()
        logger.info("🔒 Database connection closed.")
    except Exception:
        pass

    sys.exit(0)

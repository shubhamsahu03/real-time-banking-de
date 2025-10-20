import snowflake.connector

conn = snowflake.connector.connect(
    user="SHUBHAM321456",
    password="Hello_World_1234",
    account="vb90327.ap-southeast-1",
    warehouse="COMPUTE_WH",
    database="banking",
    schema="raw"
)

cs = conn.cursor()
cs.execute("SELECT CURRENT_VERSION()")
print(cs.fetchone())

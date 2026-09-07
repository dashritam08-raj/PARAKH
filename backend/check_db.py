from app.database import get_connection

connection = get_connection()

tables = connection.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

print("PARAKH database tables:")

for table in tables:
    print("-", table["name"])

connection.close()
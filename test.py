import pyodbc

conn = pyodbc.connect(
    r"Driver={ODBC Driver 17 for SQL Server};"
    r"Server=10.10.0.91\BDSERVER;"
    r"Database=Localizacion;"
    r"UID=susana;"
    r"PWD=Susana123;"
)
print("Conexión exitosa")
conn.close()
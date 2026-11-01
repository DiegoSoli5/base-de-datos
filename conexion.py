import mysql.connector

# 1. Conexión a MySQL
conexion = mysql.connector.connect(
host="localhost",
port=3306,
user="root",
password="Gauss123",
database="MiUniversidad",
)

# 2. Cursor
cursor = conexion.cursor()

# 3. Consulta
sql = "SELECT * FROM Alumnos;"
cursor.execute(sql)

# 4. Obtener datos
resultados = cursor.fetchall()

# 5. Mostrar datos
print("\n--- LISTA DE ALUMNOS ---\n")

for fila in resultados:
    print(f"Matricula: {fila[0]} | Nombre: {fila[1]} | Edad: {fila[2]}  | Email: {fila[3]}  | fecha_registro {fila[4]}")

# 6. Cerrar conexión
conexion.close()
import mysql.connector



# 1. Conexión a MySQL
conexion = mysql.connector.connect(
port=3306,
host="localhost",
user="root",
password="Gauss123",
database="MiUniversidad",
)


# 2. Cursor
cursor = conexion.cursor()

# 3. Consulta SQL
consulta = """
INSERT INTO Alumnos
(nombre, edad, email)
VALUES (%s, %s, %s)
"""

# 4. Datos (tupla)
datos = (
"Juan Chambas",
21,
"juan@email.com",
)

# 5. Ejecutar
cursor.execute(consulta, datos)

# 6. Guardar cambios
conexion.commit()

print("Alumno guardado correctamente")


if conexion.is_connected():
    conexion.close()
print("🔒 Conexión cerrada")


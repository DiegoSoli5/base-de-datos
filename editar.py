import mysql.connector


nuevo_nombre = "Juan sin Chamba (Corregido)"
matricula = 22


# 1. Conexión
conexion = mysql.connector.connect(
host="localhost",
port=3306,
user="root",
password="Gauss123",
database="MiUniversidad",
)

# 2. Cursor
cursor = conexion.cursor()

# 3. Consulta UPDATE (CORRECTA)
sql = "UPDATE Alumnos SET nombre = %s WHERE matricula = %s"

# 4. Valores
valores = (nuevo_nombre, matricula)

# 5. Ejecutar
cursor.execute(sql, valores)

# 6. Guardar cambios
conexion.commit()

# 7. Verificar filas afectadas
print(f" Se actualizaron {cursor.rowcount} registro(s).")




if conexion.is_connected():
    conexion.close()
print("Conexión cerrada")
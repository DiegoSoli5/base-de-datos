import os
import pandas as pd
import mysql.connector

# ==========================================
# 1. CARGA DE DATOS
# ==========================================
# Obtenemos la ruta del archivo CSV dentro de la carpeta data
ruta_csv = os.path.join(os.path.dirname(__file__), "clientes_inteligencia_financiera_dirty.csv")
df = pd.read_csv(ruta_csv)

print("Datos originales cargados:", len(df), "filas")


# ==========================================
# 2. LIMPIEZA DE DATOS (CON PANDAS)
# ==========================================

# Limpieza 1: Eliminar registros duplicados por id_cliente
df = df.drop_duplicates(subset=["id_cliente"], keep="first")

# Limpieza 2: Quitar espacios en blanco y estandarizar nombres y segmentos
df["nombre_cliente"] = df["nombre_cliente"].astype(str).str.strip().str.title()
df["segmento_cliente"] = df["segmento_cliente"].astype(str).str.strip().str.title()
df["segmento_cliente"] = df["segmento_cliente"].replace({"Desconocido": None, "Nan": None})

# Función auxiliar simple para limpiar columnas con formato de dinero ($ y comas)
def limpiar_dinero(serie):
    return (
        serie.astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )

# Limpieza 3: Limpiar montos monetarios (ingreso, patrimonio, portafolio)
df["ingreso_mensual_usd"] = pd.to_numeric(limpiar_dinero(df["ingreso_mensual_usd"]), errors="coerce")
df["patrimonio_estimado_usd"] = pd.to_numeric(limpiar_dinero(df["patrimonio_estimado_usd"]), errors="coerce")
# Si el portafolio viene con valores negativos, tomamos el valor absoluto
df["valor_portafolio_usd"] = pd.to_numeric(limpiar_dinero(df["valor_portafolio_usd"]), errors="coerce").abs()

# Limpieza 4: Corregir rendimiento anual (si viene un valor como 8500.0 -> 85.0)
df["rendimiento_anual_pct"] = pd.to_numeric(df["rendimiento_anual_pct"], errors="coerce")
df.loc[df["rendimiento_anual_pct"] > 100, "rendimiento_anual_pct"] = df["rendimiento_anual_pct"] / 100

# Limpieza 5: Estandarizar producto principal y perfil de riesgo
df["producto_principal"] = df["producto_principal"].astype(str).str.strip()
df["producto_principal"] = df["producto_principal"].replace({"N/A": None, "Nan": None, "": None})

df["perfil_riesgo"] = df["perfil_riesgo"].astype(str).str.strip().str.title()
df["perfil_riesgo"] = df["perfil_riesgo"].replace({"Nan": None, "": None})

# Limpieza 6: Estandarizar la moneda de la cuenta (USD, EUR, MXN)
mapeo_monedas = {
    "US DOLLAR": "USD",
    "EURO": "EUR",
    "MXN": "MXN",
}
df["moneda_cuenta"] = df["moneda_cuenta"].astype(str).str.strip().str.upper().map(mapeo_monedas)

# Limpieza 7: Estandarizar fecha de alta a formato YYYY-MM-DD (valores desconocidos quedan como None)
df["fecha_alta_cliente"] = pd.to_datetime(df["fecha_alta_cliente"], format="mixed", errors="coerce").dt.strftime("%Y-%m-%d")

# Limpieza 8: Corregir score crediticio (valores válidos entre 300 y 850, ajustar valores como 9500.0 -> 950 o NaN)
df["score_crediticio"] = pd.to_numeric(df["score_crediticio"], errors="coerce")
df.loc[df["score_crediticio"] > 850, "score_crediticio"] = df["score_crediticio"] / 10
# Dejar como entero o None
df["score_crediticio"] = df["score_crediticio"].fillna(-1).astype(int)
df["score_crediticio"] = df["score_crediticio"].replace(-1, None)

# Limpieza 9: Reemplazar NaN de pandas por None para que MySQL guarde NULL correctamente
df = df.where(pd.notnull(df), None)

print("Datos limpios listos para insertar:", len(df), "filas")


# ==========================================
# 3. CONEXIÓN A MYSQL (DOCKER COMPOSE)
# ==========================================
conexion = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="Gauss123",
    database="MiUniversidad",
)

cursor = conexion.cursor()


# ==========================================
# 4. CREAR TABLA EN MYSQL
# ==========================================
cursor.execute("DROP TABLE IF EXISTS Clientes;")

crear_tabla = """
CREATE TABLE Clientes (
    id_cliente VARCHAR(20) PRIMARY KEY,
    nombre_cliente VARCHAR(100) NOT NULL,
    segmento_cliente VARCHAR(50),
    ingreso_mensual_usd DECIMAL(15, 2),
    patrimonio_estimado_usd DECIMAL(15, 2),
    valor_portafolio_usd DECIMAL(15, 2),
    rendimiento_anual_pct DECIMAL(5, 2),
    producto_principal VARCHAR(50),
    perfil_riesgo VARCHAR(30),
    moneda_cuenta VARCHAR(10),
    fecha_alta_cliente DATE,
    score_crediticio INT
);
"""
cursor.execute(crear_tabla)
print("Tabla 'Clientes' creada correctamente.")


# ==========================================
# 5. INSERTAR DATOS LIMPIOS
# ==========================================
consulta_insert = """
INSERT INTO Clientes (
    id_cliente, nombre_cliente, segmento_cliente,
    ingreso_mensual_usd, patrimonio_estimado_usd, valor_portafolio_usd,
    rendimiento_anual_pct, producto_principal, perfil_riesgo,
    moneda_cuenta, fecha_alta_cliente, score_crediticio
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# Convertimos el DataFrame a lista de tuplas para insertar
filas_a_insertar = [tuple(fila) for fila in df.to_numpy()]

cursor.executemany(consulta_insert, filas_a_insertar)
conexion.commit()

print(f" {cursor.rowcount} clientes insertados exitosamente en la base de datos.")


# ==========================================
# 6. CERRAR CONEXIÓN
# ==========================================
if conexion.is_connected():
    cursor.close()
    conexion.close()
print(" Conexión cerrada con éxito.")

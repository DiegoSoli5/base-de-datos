import mysql.connector
import pandas as pd

df  = pd.read_csv(r"boxeadores_pro_dirty.csv")

print(df.head())

print(df.isnull().sum())

# eliminamos registros duplicados que tengamos en la base
df = df.dropna(subset=["nombre"])

# quitamos espacios en blanco al inicio y al finaly los convertimos a minusculas

df["nombre"] = df["nombre"].astype(str).str.strip().str.lower()

print(df["guardia"].unique())


print(df.isnull().sum())

for i in df["derrotas"]:
    a = 0
    if i == 0:
        a += 1

print(a)

conexion = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Gauss123",
    database="MiUniversidad"
)


cursor = conexion.cursor()

a = 
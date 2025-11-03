import pyodbc
import os
import time
import platform
from datetime import datetime

# Carga de configuración desde variables de entorno
server   = os.getenv('SQL_SERVER', 'mssql-139410-0.cloudclusters.net,10111')
database = os.getenv('SQL_DATABASE', 'autokorea')
username = os.getenv('SQL_USERNAME', 'APQ')
password = os.getenv('SQL_PASSWORD', 'Xmen2030*')

def obtener_driver_odbc():
    sistema = platform.system()
    if sistema == "Windows":
        return "ODBC Driver 17 for SQL Server"
    elif sistema == "Linux":
        return "ODBC Driver 17 for SQL Server"
    else:
        print(f"⚠️ Sistema operativo no reconocido: {sistema}")
        return "SQL Server"

def conectar_sqlserver():
    max_intentos = 5
    intento = 0
    driver = obtener_driver_odbc()

    while intento < max_intentos:
        try:
            t0_con = time.perf_counter()
            conn = pyodbc.connect(
                f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};'
                f'UID={username};PWD={password};'
                'MARS_Connection=yes;Connection Timeout=120;',
                autocommit=True,
                timeout=120
            )
            print(f"✅ Conexión exitosa a SQL Server usando driver [{driver}] ⏱️ Duración: {time.perf_counter() - t0_con:.4f}s")
            return conn
        except pyodbc.Error as e:
            intento += 1
            print(f"❌ Error de conexión con driver [{driver}]: {str(e)}. Reintentando en 5 segundos...")
            time.sleep(5)

    print("❌ No se pudo establecer la conexión tras varios intentos.")
    return None

def is_connection_active(conn):
    try:
        t0_check = time.perf_counter()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        print(f"✅ Validación de conexión activa ⏱️ Duración: {time.perf_counter() - t0_check:.4f}s")
        return True
    except Exception as e:
        print(f"⚠️ Conexión inválida: {str(e)}")
        return False

def ejecutar_consulta(query, parametros=None, modo="lectura"):
    conn = conectar_sqlserver()
    if conn is None:
        return None, []

    try:
        cursor = conn.cursor()
        try:
            cursor.timeout = 120
        except Exception:
            pass
        t0_exec = time.perf_counter()
        if parametros:
            cursor.execute(query, parametros)
        else:
            cursor.execute(query)
        print(f"📤 cursor.execute completado ⏱️ Duración: {time.perf_counter() - t0_exec:.4f}s")

        if modo == "lectura":
            if cursor.description:
                columnas = [desc[0] for desc in cursor.description]
                resultado = cursor.fetchall()
                return resultado, columnas
            return None, []

        elif modo == "escritura":
            conn.commit()
            return None, []

    except pyodbc.Error as e:
        if "08S01" in str(e):
            print("🔄 Reconectando por error de comunicación...")
            conn = conectar_sqlserver()
            return ejecutar_consulta(query, parametros, modo)

        print("❌ Error al ejecutar consulta:", str(e))
        return None, []

def obtener_cursor():
    conn = conectar_sqlserver()
    return conn.cursor() if conn else None

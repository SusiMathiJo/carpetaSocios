from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pyodbc

app = FastAPI(title="API Nacionalidades")

# Permitir llamadas desde la página estática
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos desde /static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Modelo para recibir datos (POST / PUT)
class NacionalidadIn(BaseModel):
    nombrepais: str
    nombrenacionalidad: str

# Conexión a SQL Server
def get_connection():
    return pyodbc.connect(
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=10.10.0.91\BDSERVER;"
        r"DATABASE=Localizacion;"
        r"UID=susana;"
        r"PWD=Susana123;"
    )

# Listar todas las nacionalidades
@app.get("/nacionalidades")
def listar_nacionalidades():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT CodigoPais, NombrePais, NombreNacionalidad, Usuario, WS, Tiempo
        FROM dbo.Nacionalidades
        ORDER BY CodigoPais
    """)
    filas = cur.fetchall()
    cur.close()
    conn.close()

    resultados = []
    for f in filas:
        tiempo = f[5]
        resultados.append({
            "CodigoPais": f[0],
            "NombrePais": f[1],
            "NombreNacionalidad": f[2],
            "Usuario": f[3],
            "WS": f[4],
            "Tiempo": tiempo.strftime("%Y-%m-%d %H:%M:%S") if tiempo else None
        })
    return resultados

# Agregar nueva nacionalidad (SP con @bandera=1)
@app.post("/nacionalidades")
def crear_nacionalidad(n: NacionalidadIn):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            DECLARE @CodigoPais INT, @SaveError INT;
            EXEC dbo.registronacionalidades
                @bandera = 1,
                @codigoPais = @CodigoPais OUTPUT,
                @nombrepais = ?,
                @nombrenacionalidad = ?,
                @saveError = @SaveError OUTPUT;
            SELECT @CodigoPais AS CodigoPais, @SaveError AS SaveError;
        """, (n.nombrepais, n.nombrenacionalidad))

        row = cur.fetchone()
        conn.commit()
        if not row:
            raise HTTPException(status_code=500, detail="No se obtuvo respuesta del SP.")

        codigo = row[0]
        saveError = row[1]

        if saveError != 0:
            raise HTTPException(status_code=400, detail=f"SP devolvió error: {saveError}")

        # devolver el registro insertado
        cur.execute("SELECT CodigoPais, NombrePais, NombreNacionalidad, Usuario, WS, Tiempo FROM dbo.Nacionalidades WHERE CodigoPais = ?", (codigo,))
        nueva = cur.fetchone()
        return {
            "mensaje": "Grabado correctamente",
            "CodigoPais": codigo,
            "registro": {
                "CodigoPais": nueva[0],
                "NombrePais": nueva[1],
                "NombreNacionalidad": nueva[2],
                "Usuario": nueva[3],
                "WS": nueva[4],
                "Tiempo": nueva[5].strftime("%Y-%m-%d %H:%M:%S") if nueva[5] else None
            }
        }

    except pyodbc.Error as ex:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(ex))
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# Modificar nacionalidad (SP con @bandera=2)
@app.put("/nacionalidades/{codigo}")
def modificar_nacionalidad(codigo: int, n: NacionalidadIn):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            DECLARE @SaveError INT;
            EXEC dbo.registronacionalidades
                @bandera = 2,
                @codigoPais = ?,
                @nombrepais = ?,
                @nombrenacionalidad = ?,
                @saveError = @SaveError OUTPUT;
            SELECT @SaveError AS SaveError;
        """, (codigo, n.nombrepais, n.nombrenacionalidad))

        row = cur.fetchone()
        conn.commit()
        if not row:
            raise HTTPException(status_code=500, detail="No se obtuvo respuesta del SP.")

        saveError = row[0]
        # Solo lanzar error si saveError < 0 (o tu SP define otro código de error real)
        if saveError is not None and saveError < 0:
            raise HTTPException(status_code=400, detail=f"SP devolvió error: {saveError}")

        # devolver registro actualizado
        cur.execute("SELECT CodigoPais, NombrePais, NombreNacionalidad, Usuario, WS, Tiempo FROM dbo.Nacionalidades WHERE CodigoPais = ?", (codigo,))
        reg = cur.fetchone()
        return {
            "mensaje": "Modificado correctamente",
            "registro": {
                "CodigoPais": reg[0],
                "NombrePais": reg[1],
                "NombreNacionalidad": reg[2],
                "Usuario": reg[3],
                "WS": reg[4],
                "Tiempo": reg[5].strftime("%Y-%m-%d %H:%M:%S") if reg[5] else None
            }
        }

    except pyodbc.Error as ex:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(ex))
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass
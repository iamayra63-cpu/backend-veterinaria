from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
from datetime import datetime

app = FastAPI()

def get_db_connection():
    conn = sqlite3.connect('veterinaria.db')
    conn.row_factory = sqlite3.Row
    return conn

# Modelos
class ServicioIn(BaseModel):
    nombre: str
    costo: float

class ServicioOut(BaseModel):
    id: int
    nombre: str
    costo: float

class AtencionIn(BaseModel):
    duenio: str
    mascota: str
    servicio_id: int

class AtencionOut(BaseModel):
    id: int
    duenio: str
    mascota: str
    servicio: str
    costo: float
    fecha: str

# Inicializar la base de datos
@app.on_event("startup")
def startup():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS servicios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        costo REAL NOT NULL
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS atenciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        duenio TEXT NOT NULL,
        mascota TEXT NOT NULL,
        servicio_id INTEGER NOT NULL,
        fecha TEXT NOT NULL,
        FOREIGN KEY(servicio_id) REFERENCES servicios(id)
    )''')
    conn.commit()
    conn.close()

# Endpoint para agregar servicios
@app.post("/servicios", response_model=ServicioOut)
def agregar_servicio(servicio: ServicioIn):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO servicios (nombre, costo) VALUES (?, ?)",
        (servicio.nombre, servicio.costo)
    )
    conn.commit()
    servicio_id = cursor.lastrowid
    conn.close()
    return {"id": servicio_id, "nombre": servicio.nombre, "costo": servicio.costo}

# Endpoint para listar servicios
@app.get("/servicios", response_model=List[ServicioOut])
def listar_servicios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, costo FROM servicios")
    servicios = cursor.fetchall()
    conn.close()
    return [dict(s) for s in servicios]

# Endpoint para agregar una atención
@app.post("/atenciones", response_model=AtencionOut)
def agregar_atencion(atencion: AtencionIn):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Verificar que el servicio existe
    cursor.execute("SELECT nombre, costo FROM servicios WHERE id = ?", (atencion.servicio_id,))
    servicio = cursor.fetchone()
    if not servicio:
        conn.close()
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    fecha = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO atenciones (duenio, mascota, servicio_id, fecha) VALUES (?, ?, ?, ?)",
        (atencion.duenio, atencion.mascota, atencion.servicio_id, fecha)
    )
    atencion_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {
        "id": atencion_id,
        "duenio": atencion.duenio,
        "mascota": atencion.mascota,
        "servicio": servicio["nombre"],
        "costo": servicio["costo"],
        "fecha": fecha
    }

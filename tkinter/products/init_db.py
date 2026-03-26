# Script para crear la db en sqlite. 
# Es necesario haber instalado previamente tkinter y sqlite3 en el sistema (apt install python3-tk sqlite3 libsqlite3-dev -y)

import sqlite3

db_name = "database.db"

# Conectar (crea el archivo si no existe)
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

# Crear la tabla 'producto'
cursor.execute("""
CREATE TABLE IF NOT EXISTS producto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    precio REAL NOT NULL
)
""")

conn.commit()
conn.close()

print(f"✅ Base de datos '{db_name}' creada y tabla 'producto' inicializada")

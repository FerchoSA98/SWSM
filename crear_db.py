import sqlite3

# Conexión a la base de datos (se crea si no existe)
conn = sqlite3.connect('basedatos.db')
cursor = conn.cursor()

# Crear tabla de usuarios
cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# Crear tabla de ventas
cursor.execute('''
CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT UNIQUE NOT NULL,
    efectivo REAL NOT NULL,
    tarjeta REAL NOT NULL,
    transferencia REAL NOT NULL,
    tarjeta_neto REAL NOT NULL,
    total_dia REAL NOT NULL
)
''')

# Insertar un usuario por defecto (usuario: admin, contraseña: admin)
import hashlib
password_hash = hashlib.sha256("admin".encode()).hexdigest()
cursor.execute("INSERT OR IGNORE INTO usuarios (username, password) VALUES (?, ?)", ("admin", password_hash))

# Guardar cambios y cerrar conexión
conn.commit()
conn.close()

print("Base de datos creada correctamente con un usuario: admin / admin")

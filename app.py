# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'  # Cámbiala en producción

def get_db_connection():
    conn = sqlite3.connect('ventas.db')
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    if not os.path.exists('ventas.db'):
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT UNIQUE NOT NULL,
                efectivo REAL NOT NULL,
                tarjeta REAL NOT NULL,
                transferencia REAL NOT NULL,
                tarjeta_neto REAL NOT NULL,
                total_dia REAL NOT NULL
            )
        ''')

        hashed_pw = generate_password_hash("admin")
        cursor.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)", ("admin", hashed_pw))

        conn.commit()
        conn.close()

# Decorador para proteger rutas

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'usuario' in session:
            return f(*args, **kwargs)
        return redirect(url_for('login'))
    return wrap

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['usuario'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Usuario o contraseña incorrectos')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    ventas = conn.execute('SELECT * FROM ventas ORDER BY fecha DESC').fetchall()
    conn.close()
    return render_template('index.html', ventas=ventas)

@app.route('/registrar_venta', methods=['POST'])
@login_required
def registrar_venta():
    fecha = request.form['fecha']
    efectivo = float(request.form['efectivo'])
    tarjeta = float(request.form['tarjeta'])
    transferencia = float(request.form['transferencia'])

    tarjeta_neto = round(tarjeta * (1 - 0.0417), 2)
    total_dia = round(efectivo + tarjeta_neto + transferencia, 2)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM ventas WHERE fecha = ?', (fecha,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'status': 'error', 'message': 'Ya existe un registro para esa fecha'}), 400

    cursor.execute('''
        INSERT INTO ventas (fecha, efectivo, tarjeta, transferencia, tarjeta_neto, total_dia)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (fecha, efectivo, tarjeta, transferencia, tarjeta_neto, total_dia))

    conn.commit()
    conn.close()

    return jsonify({'status': 'success', 'message': 'Venta registrada exitosamente'})

@app.route('/cambiar_contrasena', methods=['GET', 'POST'])
@login_required
def cambiar_contrasena():
    if request.method == 'POST':
        actual = request.form['actual']
        nueva = request.form['nueva']
        confirmar = request.form['confirmar']

        if nueva != confirmar:
            return render_template('cambiar_contrasena.html', error='Las contraseñas no coinciden')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE username = ?', (session['usuario'],)).fetchone()

        if user and check_password_hash(user['password'], actual):
            hashed_new = generate_password_hash(nueva)
            conn.execute('UPDATE usuarios SET password = ? WHERE id = ?', (hashed_new, user['id']))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

        conn.close()
        return render_template('cambiar_contrasena.html', error='Contraseña actual incorrecta')

    return render_template('cambiar_contrasena.html')

if __name__ == '__main__':
    initialize_db()
    app.run(debug=True)
@app.route('/registrar_venta', methods=['POST'])
@login_required
def registrar_venta():
    fecha = request.form['fecha']
    efectivo = float(request.form['efectivo'])
    tarjeta = float(request.form['tarjeta'])
    transferencia = float(request.form['transferencia'])

    tarjeta_neto = round(tarjeta * (1 - 0.0417), 2)
    total_dia = round(efectivo + tarjeta_neto + transferencia, 2)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM ventas WHERE fecha = ?', (fecha,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'status': 'error', 'message': 'Ya existe un registro para esa fecha'}), 400

    cursor.execute('''
        INSERT INTO ventas (fecha, efectivo, tarjeta, transferencia, tarjeta_neto, total_dia)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (fecha, efectivo, tarjeta, transferencia, tarjeta_neto, total_dia))

    conn.commit()
    conn.close()

    return jsonify({'status': 'success', 'message': 'Venta registrada exitosamente'})

from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'clave_secreta_sushi'  # Cambia esto por algo más complejo si deseas

def get_db_connection():
    conn = sqlite3.connect('ventas.db')
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    if not os.path.exists('ventas.db'):
        conn = get_db_connection()
        # Tabla de ventas
        conn.execute('''
            CREATE TABLE ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT,
                efectivo REAL,
                tarjeta REAL,
                transferencia REAL
            )
        ''')
        # Tabla de usuarios
        conn.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        # Usuario admin (admin / admin123)
        hashed_password = generate_password_hash('admin123')
        conn.execute('INSERT INTO usuarios (username, password) VALUES (?, ?)', ('admin', hashed_password))
        conn.commit()
        conn.close()

# Middleware: bloquear acceso si no hay sesión
@app.before_request
def require_login():
    rutas_libres = ['login', 'cambiar_contrasena']
    if 'usuario' not in session and request.endpoint not in rutas_libres and not request.endpoint.startswith('static'):
        return redirect('/login')

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
            return redirect('/')
        else:
            return render_template('login.html', error='Usuario o contraseña incorrectos')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        fecha = request.form['fecha']
        efectivo = request.form['efectivo']
        tarjeta = request.form['tarjeta']
        transferencia = request.form['transferencia']

        conn = get_db_connection()
        conn.execute('INSERT INTO ventas (fecha, efectivo, tarjeta, transferencia) VALUES (?, ?, ?, ?)',
                     (fecha, efectivo, tarjeta, transferencia))
        conn.commit()
        conn.close()
        return redirect('/')

    conn = get_db_connection()
    ventas = conn.execute('SELECT * FROM ventas').fetchall()
    conn.close()
    return render_template('index.html', ventas=ventas)

# Ruta para cambiar la contraseña
@app.route('/cambiar_contrasena', methods=['GET', 'POST'])
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
            hashed_new_password = generate_password_hash(nueva)
            conn.execute('UPDATE usuarios SET password = ? WHERE id = ?', (hashed_new_password, user['id']))
            conn.commit()
            conn.close()
            return redirect('/')

        conn.close()
        return render_template('cambiar_contrasena.html', error='Contraseña actual incorrecta')

    return render_template('cambiar_contrasena.html')

if __name__ == '__main__':
    initialize_db()
    app.run(debug=True)

#Ruta para registrar una venta
@app.route('/registrar_venta', methods=['POST'])
@login_required
def registrar_venta():
    fecha = request.form['fecha']
    efectivo = float(request.form['efectivo'])
    tarjeta = float(request.form['tarjeta'])
    transferencia = float(request.form['transferencia'])

    tarjeta_neto = round(tarjeta * (1 - 0.0417), 2)
    total_dia = round(efectivo + tarjeta_neto + transferencia, 2)

    conn = sqlite3.connect('basedatos.db')
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


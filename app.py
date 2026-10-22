from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Función para conectar a la Base de Datos SQLite (crea automáticamente el archivo cyberguard.db)
def conectar_db():
    conexion = sqlite3.connect('cyberguard.db')
    conexion.row_factory = sqlite3.Row
    return conexion

# Crear la tabla de usuarios si no existe
def inicializar_db():
    conexion = conectar_db()
    conexion.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            usuario TEXT UNIQUE NOT NULL,
            correo TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conexion.commit()
    conexion.close()

# Ruta principal: Redirige directamente al Login
@app.route('/')
def inicio():
    return redirect(url_for('login'))

# Ruta para el Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        
        conexion = conectar_db()
        cursor = conexion.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE usuario = ? AND password = ?', (usuario, password))
        user = cursor.fetchone()
        conexion.close()
        
        if user:
            return f"<h1>¡Inicio de sesión exitoso!</h1><p>Bienvenido a CyberGuard, <b>{user['nombre']}</b>.</p>"
        else:
            return "<h1>Error</h1><p>Usuario o contraseña incorrectos. <a href='/login'>Intentar de nuevo</a></p>"
            
    return render_template('login.html')

# Ruta para el Registro
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        usuario = request.form['usuario']
        correo = request.form['correo']
        password = request.form['password']
        
        # Validación requerida en el algoritmo/pseudocódigo (Mínimo 8 caracteres)
        if len(password) < 8:
            return "<h1>Error</h1><p>La contraseña debe tener al menos 8 caracteres. <a href='/registro'>Intentar de nuevo</a></p>"
            
        try:
            conexion = conectar_db()
            cursor = conexion.cursor()
            cursor.execute('INSERT INTO usuarios (nombre, usuario, correo, password) VALUES (?, ?, ?, ?)',
                           (nombre, usuario, correo, password))
            conexion.commit()
            conexion.close()
            return "<h1>¡Cuenta creada con éxito!</h1><p><a href='/login'>Haz clic aquí para iniciar sesión</a></p>"
        except sqlite3.IntegrityError:
            return "<h1>Error</h1><p>El usuario ya existe. Intenta con otro. <a href='/registro'>Intentar de nuevo</a></p>"
            
    return render_template('registro.html')

if __name__ == '__main__':
    inicializar_db()
    print("Iniciando servidor de CyberGuard...")
    app.run(debug=True)
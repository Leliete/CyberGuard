from flask import Flask, render_template, request, redirect, url_for
import bcrypt
pyodbc = __import__('pyodbc')

app = Flask(__name__)

# Función para conectar a SQL Server con el nombre exacto de tu instancia
def conectar_db():
    conexion = pyodbc.connect(
        'DRIVER={SQL Server};'
        'SERVER=MSI\\SQLEXPRESS;'
        'DATABASE=cyberguard;'
        'Trusted_Connection=yes;'
    )
    return conexion

# Crear la tabla de usuarios en SQL Server si no existe
def inicializar_db():
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'usuarios')
        CREATE TABLE usuarios (
            id INT IDENTITY(1,1) PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            usuario VARCHAR(255) NOT NULL UNIQUE,
            correo VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    ''')
    conexion.commit()
    conexion.close()

# Ruta principal: Redirige al Login
@app.route('/')
def inicio():
    return redirect(url_for('login'))

# Ruta para el Login (verificando con Bcrypt)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password_ingresada = request.form['password']
        
        conexion = conectar_db()
        cursor = conexion.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE usuario = ?', (usuario,))
        user = cursor.fetchone()
        conexion.close()
        
        # Verificamos la contraseña usando bcrypt
        if user and bcrypt.checkpw(password_ingresada.encode('utf-8'), user.password.encode('utf-8')):
            return redirect(url_for('evaluacion'))
        else:
            return "<h1>Error</h1><p>Usuario o contraseña incorrectos. <a href='/login'>Intentar de nuevo</a></p>"
            
    return render_template('login.html')

# Ruta para el Registro (generando hash con Bcrypt)
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        usuario = request.form['usuario']
        correo = request.form['correo']
        password_plana = request.form['password']
        
        # Validación de longitud mínima (mínimo 8 caracteres)
        if len(password_plana) < 8:
            return "<h1>Error</h1><p>La contraseña debe tener al menos 8 caracteres. <a href='/registro'>Intentar de nuevo</a></p>"
            
        # Generar el hash seguro de la contraseña usando bcrypt
        salt = bcrypt.gensalt()
        password_hashed = bcrypt.hashpw(password_plana.encode('utf-8'), salt).decode('utf-8')
            
        try:
            conexion = conectar_db()
            cursor = conexion.cursor()
            cursor.execute('INSERT INTO usuarios (nombre, usuario, correo, password) VALUES (?, ?, ?, ?)',
                           (nombre, usuario, correo, password_hashed))
            conexion.commit()
            conexion.close()
            return "<h1>¡Cuenta creada con éxito!</h1><p><a href='/login'>Haz clic aquí para iniciar sesión</a></p>"
        except Exception as e:
            return f"<h1>Error</h1><p>El usuario ya existe o hubo un error en la BD. <a href='/registro'>Intentar de nuevo</a></p>"
            
    return render_template('registro.html')

# Módulo de Evaluación Diagnóstica
@app.route('/evaluacion', methods=['GET', 'POST'])
def evaluacion():
    if request.method == 'POST':
        respuestas_correctas = {
            'p1': 'A', 'p2': 'A', 'p3': 'A', 'p4': 'A', 'p5': 'A',
            'p6': 'A', 'p7': 'A', 'p8': 'A', 'p9': 'A', 'p10': 'A'
        }
        
        puntuacion = 0
        for i in range(1, 11):
            pregunta = f'p{i}'
            if request.form.get(pregunta) == respuestas_correctas[pregunta]:
                puntuacion += 1
                
        if puntuacion <= 4:
            nivel = "BÁSICO"
        elif 5 <= puntuacion <= 7:
            nivel = "INTERMEDIO"
        else:
            nivel = "AVANZADO"
            
        if puntuacion >= 8:
            return redirect(url_for('certificado', puntuacion=puntuacion))
        else:
            return f"""
            <div style="font-family: Arial; text-align: center; margin-top: 50px;">
                <h1 style="color: #1a2a3a;">¡Evaluación Completada!</h1>
                <p style="font-size: 18px;">Puntuación obtenida: <b>{puntuacion} / 10</b></p>
                <p style="font-size: 20px; color: #007bff;">Tu nivel asignado es: <b>{nivel}</b></p>
                <p>Necesitas al menos 8 aciertos para obtener tu certificado.</p>
                <br>
                <a href="/evaluacion" style="padding: 10px 15px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">Reintentar evaluación</a>
                <a href="/logout" style="padding: 10px 15px; background: #dc3545; color: white; text-decoration: none; border-radius: 5px; margin-left: 10px;">Cerrar sesión</a>
            </div>
            """
            
    return render_template('Modulo de evaluacion.html')

# Ruta para el certificado
@app.route('/certificado/<int:puntuacion>')
def certificado(puntuacion):
    return render_template('certificado.html', puntuacion=puntuacion)

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    return redirect(url_for('login'))

if __name__ == '__main__':
    inicializar_db()
    print("Iniciando servidor de CyberGuard con SQL Server y Bcrypt...")
    app.run(debug=True)

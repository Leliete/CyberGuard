from flask import Flask, render_template, request, redirect, url_for
import bcrypt
from cryptography.fernet import Fernet
pyodbc = __import__('pyodbc')

app = Flask(__name__)

# Llave de Fernet estrictamente fija y válida de 32 bytes en base64
# Esto garantiza que la misma palabra siempre cifre igual y se pueda descifrar correctamente
FERNET_KEY = b'Kk7y9R2vL5xP3mN1sQ8wZ4tA6bC0fD9gH2jK5lM8nB0='
cipher = Fernet(FERNET_KEY)

def cifrar(texto):
    if not texto:
        return ""
    return cipher.encrypt(texto.encode('utf-8')).decode('utf-8')

def descifrar(texto_cifrado):
    if not texto_cifrado:
        return ""
    try:
        return cipher.decrypt(texto_cifrado.encode('utf-8')).decode('utf-8')
    except Exception:
        return texto_cifrado # Si no se puede descifrar, regresa el texto original

# Conexión a la base de datos
def conectar_db():
    conexion = pyodbc.connect(
        'DRIVER={SQL Server};'
        'SERVER=MSI\\SQLEXPRESS;'
        'DATABASE=cyberguard;'
        'Trusted_Connection=yes;'
    )
    return conexion

# Inicializar tabla con columnas VARCHAR(MAX) para soportar cadenas cifradas largas
def inicializar_db():
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'usuarios')
        CREATE TABLE usuarios (
            id INT IDENTITY(1,1) PRIMARY KEY,
            nombre VARCHAR(MAX) NOT NULL,
            usuario VARCHAR(MAX) NOT NULL,
            correo VARCHAR(MAX) NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    ''')
    conexion.commit()
    conexion.close()

@app.route('/')
def inicio():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario_ingresado = request.form['usuario'].strip()
        password_ingresada = request.form['password']
        
        conexion = conectar_db()
        cursor = conexion.cursor()
        cursor.execute('SELECT * FROM usuarios')
        usuarios_db = cursor.fetchall()
        conexion.close()
        
        # Buscamos el usuario recorriendo la tabla y descifrando el campo de usuario
        usuario_encontrado = None
        for u in usuarios_db:
            usuario_descifrado = descifrar(u.usuario)
            if usuario_descifrado == usuario_ingresado:
                usuario_encontrado = u
                break
        
        # Verificamos la contraseña con Bcrypt
        if usuario_encontrado and bcrypt.checkpw(password_ingresada.encode('utf-8'), usuario_encontrado.password.encode('utf-8')):
            return redirect(url_for('evaluacion'))
        else:
            return "<h1>Error</h1><p>Usuario o contraseña incorrectos. <a href='/login'>Intentar de nuevo</a></p>"
            
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre_plano = request.form['nombre']
        usuario_plano = request.form['usuario'].strip()
        correo_plano = request.form['correo']
        password_plana = request.form['password']
        
        if len(password_plana) < 8:
            return "<h1>Error</h1><p>La contraseña debe tener al menos 8 caracteres. <a href='/registro'>Intentar de nuevo</a></p>"
            
        # Cifrar con Fernet
        nombre_cifrado = cifrar(nombre_plano)
        usuario_cifrado = cifrar(usuario_plano)
        correo_cifrado = cifrar(correo_plano)
        
        # Hashear password con Bcrypt
        salt = bcrypt.gensalt()
        password_hashed = bcrypt.hashpw(password_plana.encode('utf-8'), salt).decode('utf-8')
            
        try:
            conexion = conectar_db()
            cursor = conexion.cursor()
            cursor.execute('INSERT INTO usuarios (nombre, usuario, correo, password) VALUES (?, ?, ?, ?)',
                           (nombre_cifrado, usuario_cifrado, correo_cifrado, password_hashed))
            conexion.commit()
            conexion.close()
            # Redirección limpia hacia el login
            return redirect(url_for('login'))
        except Exception as e:
            return f"<h1>Error</h1><p>Hubo un error en la BD: {e}. <a href='/registro'>Intentar de nuevo</a></p>"
            
    return render_template('registro.html')

@app.route('/evaluacion', methods=['GET', 'POST'])
def evaluacion():
    if request.method == 'POST':
        # RESPUESTAS CORRECTAS ACTUALIZADAS SEGÚN EL NUEVO ORDEN DE LAS OPCIONES
        respuestas_correctas = {
            'p1': 'B',
            'p2': 'C',
            'p3': 'D',
            'p4': 'A',
            'p5': 'B',
            'p6': 'C',
            'p7': 'D',
            'p8': 'A',
            'p9': 'B',
            'p10': 'C'
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

@app.route('/certificado/<int:puntuacion>')
def certificado(puntuacion):
    return render_template('certificado.html', puntuacion=puntuacion)

@app.route('/logout')
def logout():
    return redirect(url_for('login'))

if __name__ == '__main__':
    inicializar_db()
    print("Iniciando servidor de CyberGuard con clave estática de Fernet...")
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for
import bcrypt
from cryptography.fernet import Fernet
pyodbc = __import__('pyodbc')

app = Flask(__name__)

# Llave de Fernet estrictamente fija y válida de 32 bytes en base64
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

# Inicializar tabla de usuarios con columnas de progreso
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
            password VARCHAR(255) NOT NULL,
            nivel_actual VARCHAR(50) DEFAULT 'diagnostico',
            puntuacion_actual INT DEFAULT 0
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
        
        usuario_encontrado = None
        for u in usuarios_db:
            usuario_descifrado = descifrar(u.usuario)
            if usuario_descifrado == usuario_ingresado:
                usuario_encontrado = u
                break
        
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
            
        nombre_cifrado = cifrar(nombre_plano)
        usuario_cifrado = cifrar(usuario_plano)
        correo_cifrado = cifrar(correo_plano)
        
        salt = bcrypt.gensalt()
        password_hashed = bcrypt.hashpw(password_plana.encode('utf-8'), salt).decode('utf-8')
            
        try:
            conexion = conectar_db()
            cursor = conexion.cursor()
            cursor.execute('INSERT INTO usuarios (nombre, usuario, correo, password, nivel_actual, puntuacion_actual) VALUES (?, ?, ?, ?, ?, ?)',
                           (nombre_cifrado, usuario_cifrado, correo_cifrado, password_hashed, 'diagnostico', 0))
            conexion.commit()
            conexion.close()
            return redirect(url_for('login'))
        except Exception as e:
            return f"<h1>Error</h1><p>Hubo un error en la BD: {e}. <a href='/registro'>Intentar de nuevo</a></p>"
            
    return render_template('registro.html')

@app.route('/evaluacion', methods=['GET', 'POST'])
def evaluacion():
    if request.method == 'POST':
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
                
        # LÓGICA DE SALTO DE NIVELES:
        if puntuacion >= 8:
            # Sobresaliente: Salta directo al certificado final
            return redirect(url_for('certificado', puntuacion=puntuacion))
        elif 5 <= puntuacion <= 7:
            # Nivel Intermedio
            return redirect(url_for('nivel_intermedio'))
        else:
            # Nivel Básico (1 a 4 aciertos)
            return redirect(url_for('nivel_basico'))
            
    return render_template('Modulo de evaluacion.html')

# ==========================================
# RUTAS DE HISTORIAS Y NIVELES
# ==========================================

@app.route('/nivel/basico')
def nivel_basico():
    return render_template('historia_basico.html')

@app.route('/evaluacion/basico', methods=['GET', 'POST'])
def evaluacion_basico():
    if request.method == 'POST':
        respuestas_correctas_basico = {
            'bp1': 'B',
            'bp2': 'A',
            'bp3': 'B',
            'bp4': 'B',
            'bp5': 'C',
            'bp6': 'B',
            'bp7': 'A',
            'bp8': 'B',
            'bp9': 'B',
            'bp10': 'B'
        }
        
        puntuacion = 0
        for i in range(1, 11):
            preq = f'bp{i}'
            if request.form.get(preq) == respuestas_correctas_basico[preq]:
                puntuacion += 1
                
        # Aprobatorio: de 8 a 10 aciertos
        if puntuacion >= 8:
            return redirect(url_for('certificado_basico'))
        else:
            return f"""
            <div style="font-family: 'Rajdhani', sans-serif; background: #061526; color: white; text-align: center; padding-top: 100px; min-height: 100vh;">
                <h1 style="color: #ff4545; font-family: 'Orbitron', sans-serif;">Nivel Básico No Superado</h1>
                <p style="font-size: 18px;">Obtuviste <b>{puntuacion} / 10</b> aciertos.</p>
                <p>Necesitas al menos 8 aciertos para completar este nivel y obtener tu certificado.</p>
                <br>
                <a href="/evaluacion/basico" style="padding: 12px 25px; background: #087cff; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">Reintentar Evaluación</a>
                <br><br><br>
                <a href="/evaluacion" style="color: #72cfff; text-decoration: none; font-size: 14px;">🚪 Volver al Módulo Principal</a>
            </div>
            """
            
    return render_template('evaluacion_basico.html')

@app.route('/certificado/basico')
def certificado_basico():
    return render_template('certificado_basico.html')

@app.route('/nivel/intermedio')
def nivel_intermedio():
    return render_template('historia_intermedio.html')

@app.route('/nivel/avanzado')
def nivel_avanzado():
    return render_template('historia_avanzado.html')

@app.route('/certificado/<int:puntuacion>')
def certificado(puntuacion):
    return render_template('certificado.html', puntuacion=puntuacion)

@app.route('/logout')
def logout():
    return redirect(url_for('login'))

if __name__ == '__main__':
    inicializar_db()
    print("Iniciando servidor de CyberGuard...")
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import qrcode
from io import BytesIO
import base64
from dotenv import load_dotenv

# PyMySQL para resolver problemas de conexión en entorno local
import pymysql
pymysql.install_as_MySQLdb()

# Load environment variables
load_dotenv()

# Flask app initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(24).hex()

# Database configuration for PythonAnywhere
username = os.environ.get('DB_USERNAME', 'PruebasJR')
password = os.environ.get('DB_PASSWORD', 'Emprendimiento2025')
hostname = os.environ.get('DB_HOSTNAME', 'PruebasJR.mysql.pythonanywhere-services.com')
dbname = os.environ.get('DB_NAME', 'PruebasJR$GeoPet')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{username}:{password}@{hostname}/{dbname}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Update SQLAlchemy configuration with connection pooling and reconnect settings
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 280,  # Recycle connections before MySQL's default timeout of 8 hours
    'pool_timeout': 20,  # Wait up to 20 seconds for a connection from the pool
    'pool_pre_ping': True,  # Enable connection health checks before use
    'pool_size': 10,  # Set a reasonable pool size
    'max_overflow': 5,  # Allow up to 5 additional connections when pool is full
}
db = SQLAlchemy(app)

# Email configuration
USER_MAIL = "joselocochon74@gmail.com"
PASSWORD = "qrph ygfl tryr ised"

# Models
class Genero(db.Model):
    __tablename__ = 'Generos'
    ID = db.Column(db.Integer, primary_key=True)
    Descripcion = db.Column(db.String(50), nullable=False)

class Mascota(db.Model):
    __tablename__ = 'Mascotas'
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nombre = db.Column(db.String(50), nullable=False)
    Especie = db.Column(db.String(50))
    Raza = db.Column(db.String(50))
    Edad = db.Column(db.Integer)
    Dueno_ID = db.Column(db.Integer, db.ForeignKey('Usuarios.ID'), nullable=False)
    # Agregamos más campos según sea necesario

class Usuario(db.Model):
    __tablename__ = 'Usuarios'
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nombre = db.Column(db.String(50), nullable=False)
    Apellido = db.Column(db.String(50), nullable=False)
    Email = db.Column(db.String(120), unique=True, nullable=False)
    Telefono = db.Column(db.String(20), nullable=True)
    Password_Hash = db.Column(db.String(128), nullable=False)
    Genero_ID = db.Column(db.Integer, db.ForeignKey('Generos.ID'), nullable=True)
    Fecha_Registro = db.Column(db.DateTime, default=datetime.utcnow)
    Estado_Cuenta = db.Column(db.String(20), default='inactivo')
    Email_Verificado = db.Column(db.Boolean, default=False)
    Fecha_Verificacion = db.Column(db.DateTime)
    Fecha_Nacimiento = db.Column(db.Date)
    Calle = db.Column(db.String(100))
    Ciudad = db.Column(db.String(50))
    Estado_Provincia = db.Column(db.String(50))
    Codigo_Postal = db.Column(db.String(20))
    Pais = db.Column(db.String(50))
    Ultima_Conexion = db.Column(db.DateTime)
    Contador_Conexiones = db.Column(db.Integer, default=0)
    
    # Relaciones
    mascotas = db.relationship('Mascota', backref='dueno', lazy=True)
    ubicaciones = db.relationship('UbicacionGPS', backref='usuario', lazy=True)
    sesiones = db.relationship('Sesion', backref='usuario', lazy=True)
    tokens = db.relationship('TokenVerificacion', backref='usuario', lazy=True)
    
    def get_saludo(self):
        """Retorna un saludo personalizado según el género del usuario"""
        if self.Genero_ID == 1:  # Masculino
            return "Bienvenido"
        elif self.Genero_ID == 2:  # Femenino
            return "Bienvenida"
        else:  # Otro o sin género
            return "Bienvenid@"

class TokenVerificacion(db.Model):
    __tablename__ = 'Tokens_Verificacion'
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Usuario_ID = db.Column(db.Integer, db.ForeignKey('Usuarios.ID'), nullable=False)
    Token = db.Column(db.String(255), nullable=False, unique=True)
    Tipo = db.Column(db.String(20), default='email', nullable=False)
    Fecha_Creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    Fecha_Expiracion = db.Column(db.DateTime, nullable=False)
    Usado = db.Column(db.Boolean, default=False)

class UbicacionGPS(db.Model):
    __tablename__ = 'Ubicaciones_GPS'
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Usuario_ID = db.Column(db.Integer, db.ForeignKey('Usuarios.ID'), nullable=False)
    Latitud = db.Column(db.Float(10, 7), nullable=False)
    Longitud = db.Column(db.Float(10, 7), nullable=False)
    Precision_GPS = db.Column(db.Float(5, 2))
    Fecha_Registro = db.Column(db.DateTime, default=datetime.utcnow)

class Sesion(db.Model):
    __tablename__ = 'Sesiones'
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Usuario_ID = db.Column(db.Integer, db.ForeignKey('Usuarios.ID'), nullable=False)
    Inicio_Sesion = db.Column(db.DateTime, default=datetime.utcnow)
    Fin_Sesion = db.Column(db.DateTime)
    IP_Direccion = db.Column(db.String(45))
    Dispositivo = db.Column(db.String(100))
    Sistema_Operativo = db.Column(db.String(50))

# Helper functions
def send_qr_email(email, qr_img, lat, lng, user):
    """
    Envía un correo con el código QR generado al usuario.
    
    Args:
        email: Correo electrónico del destinatario
        qr_img: Imagen del código QR en formato bytes
        lat: Latitud de la ubicación
        lng: Longitud de la ubicación
        user: Objeto de usuario que generó el QR
    
    Returns:
        bool: True si el correo se envió correctamente, False en caso contrario
    """
    msg = MIMEMultipart()
    msg['From'] = USER_MAIL
    msg['To'] = email
    msg['Subject'] = "Tu código QR de GeoPet"
    
    # Obtener información del usuario
    nombre_completo = f"{user.Nombre} {user.Apellido}"
    telefono = user.Telefono or "No disponible"
    
    body = f"""
    <html>
        <body>
            <h2>Tu Código QR de GeoPet</h2>
            <p>Hola {nombre_completo},</p>
            <p>Aquí está tu código QR generado con la ubicación:</p>
            <p>Latitud: {lat}</p>
            <p>Longitud: {lng}</p>
            
            <h3>Información de contacto registrada:</h3>
            <ul>
                <li><strong>Nombre:</strong> {nombre_completo}</li>
                <li><strong>Teléfono:</strong> {telefono}</li>
                <li><strong>Email:</strong> {email}</li>
            </ul>
            
            <p>Este código contiene tu ubicación y correo electrónico.</p>
            <p>Cuando alguien escanee este código QR, recibirás una notificación con su ubicación.</p>
            <p>¡Gracias por usar GeoPet!</p>
        </body>
    </html>
    """
    
    text = MIMEText(body, 'html')
    msg.attach(text)
    
    # Attach QR code image
    img = MIMEImage(qr_img)
    img.add_header('Content-Disposition', 'attachment', filename="geopet_qrcode.png")
    msg.attach(img)
    
    # Send email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(USER_MAIL, PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_admin_qr_notification(qr_img, lat, lng, user):
    """
    Envía una notificación al administrador cuando un usuario genera un código QR.
    
    Args:
        qr_img: La imagen del código QR en formato bytes
        lat: Latitud de la ubicación
        lng: Longitud de la ubicación
        user: Objeto de usuario que generó el QR
    
    Returns:
        bool: True si el correo se envió correctamente, False en caso contrario
    """
    admin_email = "joselocochon74@gmail.com"
    
    msg = MIMEMultipart()
    msg['From'] = USER_MAIL
    msg['To'] = admin_email
    msg['Subject'] = "Nuevo código QR generado en GeoPet"
    
    # Obtener información del usuario
    nombre = user.Nombre
    apellido = user.Apellido
    email = user.Email
    telefono = user.Telefono or "No disponible"
    
    body = f"""
    <html>
        <body>
            <h2>Notificación de Generación de QR</h2>
            <p>Un usuario ha generado un nuevo código QR en GeoPet.</p>
            
            <h3>Información del Usuario:</h3>
            <ul>
                <li><strong>Nombre:</strong> {nombre} {apellido}</li>
                <li><strong>Email:</strong> {email}</li>
                <li><strong>Teléfono:</strong> {telefono}</li>
            </ul>
            
            <h3>Información de Ubicación:</h3>
            <p>Latitud: {lat}</p>
            <p>Longitud: {lng}</p>
            
            <p>El código QR se adjunta a este correo.</p>
        </body>
    </html>
    """
    
    text = MIMEText(body, 'html')
    msg.attach(text)
    
    # Attach QR code image
    img = MIMEImage(qr_img)
    img.add_header('Content-Disposition', 'attachment', filename="geopet_qrcode.png")
    msg.attach(img)
    
    # Send email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(USER_MAIL, PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending admin notification email: {str(e)}")
        return False

def send_scan_notification(email, scanner_lat, scanner_lng):
    msg = MIMEMultipart()
    msg['From'] = USER_MAIL
    msg['To'] = email
    msg['Subject'] = "Notificación: Tu código QR de GeoPet ha sido escaneado"
    
    body = f"""
    <html>
        <body>
            <h2>Notificación de Escaneo</h2>
            <p>Tu código QR de GeoPet ha sido escaneado en la ubicación:</p>
            <p>Latitud: {scanner_lat}</p>
            <p>Longitud: {scanner_lng}</p>
            <p>¡Gracias por usar GeoPet!</p>
        </body>
    </html>
    """
    
    text = MIMEText(body, 'html')
    msg.attach(text)
    
    # Send email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(USER_MAIL, PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending notification email: {str(e)}")
        return False

def generate_verification_token():
    """Generate a random verification token"""
    return os.urandom(32).hex()

def create_verification_token(user_id):
    """Create a verification token for a user"""
    token = generate_verification_token()
    # Token válido por 24 horas
    expiration = datetime.utcnow() + timedelta(hours=24)
    
    new_token = TokenVerificacion(
        Usuario_ID=user_id,
        Token=token,
        Fecha_Expiracion=expiration
    )
    
    db.session.add(new_token)
    db.session.commit()
    
    return token

def send_verification_email(email, token):
    """Send verification email to user"""
    msg = MIMEMultipart()
    msg['From'] = USER_MAIL
    msg['To'] = email
    msg['Subject'] = "Verifica tu correo electrónico - GeoPet"
    
    # Crear URL de verificación
    verification_url = url_for('verify_email', token=token, _external=True)
    
    body = f"""
    <html>
        <body>
            <h2>Bienvenido a GeoPet</h2>
            <p>Gracias por registrarte en GeoPet. Para activar tu cuenta, haz clic en el siguiente enlace:</p>
            <p><a href="{verification_url}">Verificar mi correo electrónico</a></p>
            <p>Este enlace expirará en 24 horas.</p>
            <p>Si no solicitaste esta verificación, puedes ignorar este correo.</p>
            <p>¡Gracias por usar GeoPet!</p>
        </body>
    </html>
    """
    
    text = MIMEText(body, 'html')
    msg.attach(text)
    
    # Send email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(USER_MAIL, PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar correo de verificación: {str(e)}")
        return False

def generate_qrcode(data):
    """
    Genera un código QR basado en los datos proporcionados.
    
    Args:
        data: Datos a codificar en el QR (normalmente un JSON)
    
    Returns:
        tuple: (base64_image, image_bytes)
    """
    # Parse JSON data to create a formatted URL with parameters
    qr_data = json.loads(data)
    
    # Obtener la URL base
    base_url = request.host_url.rstrip('/')
    if os.environ.get('PYTHONANYWHERE_DOMAIN'):
        # Si estamos en PythonAnywhere, usar el dominio completo
        #base_url = f"https://{os.environ.get('PYTHONANYWHERE_DOMAIN')}"
        base_url = f"https://pruebasjr.pythonanywhere.com"

    
    # Create a formatted URL that will lead to the public page when scanned
    # The URL format will work with any QR scanner
    url_data = f"{base_url}/encontrado?"
    url_data += f"email={qr_data.get('email', '')}"
    url_data += f"&lat={qr_data.get('lat', '')}"
    url_data += f"&lng={qr_data.get('lng', '')}"
    url_data += f"&nombre={qr_data.get('nombre', '')}"
    url_data += f"&telefono={qr_data.get('telefono', '')}"
    url_data += f"&mascota={qr_data.get('mascota', '')}"
    
    # Create QR code with the URL
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction
        box_size=10,
        border=4,
    )
    qr.add_data(url_data)  # Use the URL instead of raw JSON
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    img_bytes = BytesIO()
    img.save(img_bytes)
    img_bytes.seek(0)
    
    # Convert to base64 for displaying in browser
    img_b64 = BytesIO()
    img.save(img_b64)
    img_b64.seek(0)
    img_b64_str = base64.b64encode(img_b64.getvalue()).decode('utf-8')
    
    return img_b64_str, img_bytes.getvalue()

def record_session(user_id, request):
    """Record user session details"""
    new_session = Sesion(
        Usuario_ID=user_id,
        IP_Direccion=request.remote_addr,
        Dispositivo=request.user_agent.string,
        Sistema_Operativo=request.user_agent.platform
    )
    db.session.add(new_session)
    db.session.commit()
    
    # Store session ID in Flask session
    session['session_id'] = new_session.ID
    return new_session.ID

def update_session_end(session_id):
    """Update session end time"""
    user_session = Sesion.query.get(session_id)
    if user_session:
        user_session.Fin_Sesion = datetime.utcnow()
        db.session.commit()

def notify_qr_scan(owner_email, scanner_ip):
    """
    Notifica al propietario que su código QR ha sido escaneado.
    
    Args:
        owner_email: Email del propietario del QR
        scanner_ip: Dirección IP de quien escaneó el QR
    
    Returns:
        bool: True si la notificación se envió correctamente, False en caso contrario
    """
    try:
        # Get the approximate location of the scanner
        try:
            scanner_location = get_location_from_ip(scanner_ip)
            location_text = f"Ubicación aproximada: {scanner_location.get('city', 'Desconocida')}, {scanner_location.get('country_name', 'País desconocido')}"
        except:
            location_text = "No se pudo determinar la ubicación del escáner"
        
        # Obtener la fecha y hora actual en formato legible
        now = datetime.now()
        fecha_escaneo = now.strftime("%d/%m/%Y %H:%M:%S")
        
        msg = MIMEMultipart()
        msg['From'] = USER_MAIL
        msg['To'] = owner_email
        msg['Subject'] = "¡Tu código QR de GeoPet ha sido escaneado!"
        
        body = f"""
        <html>
            <body>
                <h2>Notificación de Escaneo de QR</h2>
                <p>Hola,</p>
                <p>Tu código QR de GeoPet ha sido escaneado por alguien.</p>
                <p><strong>Fecha y hora:</strong> {fecha_escaneo}</p>
                <p><strong>{location_text}</strong></p>
                <p>Es posible que esta persona se ponga en contacto contigo pronto.</p>
                <p>Si no reconoces esta actividad, puedes ignorar este mensaje.</p>
                <br>
                <p>Saludos,</p>
                <p>El equipo de GeoPet</p>
            </body>
        </html>
        """
        
        text = MIMEText(body, 'html')
        msg.attach(text)
        
        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(USER_MAIL, PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error notifying owner: {str(e)}")
        return False

def get_location_from_ip(ip_address):
    """
    Obtiene información de localización aproximada basada en una dirección IP.
    
    Args:
        ip_address: La dirección IP para la geocodificación
        
    Returns:
        dict: Diccionario con información de la ubicación (ciudad, país, etc.)
    """
    try:
        # Para IPs locales, devolver información predeterminada
        if ip_address in ('127.0.0.1', 'localhost', '::1') or ip_address.startswith('192.168.') or ip_address.startswith('10.'):
            return {
                'city': 'Local',
                'country_name': 'Red local',
                'latitude': 0,
                'longitude': 0
            }
        
        # Usar un servicio gratuito de geolocalización de IP
        import requests
        response = requests.get(f'https://ipapi.co/{ip_address}/json/')
        if response.status_code == 200:
            return response.json()
        return {
            'city': 'Desconocida',
            'country_name': 'Desconocido',
            'latitude': 0,
            'longitude': 0
        }
    except Exception:
        # En caso de error, devolver información predeterminada
        return {
            'city': 'Desconocida',
            'country_name': 'Desconocido',
            'latitude': 0,
            'longitude': 0
        }

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = Usuario.query.filter_by(Email=email).first()
        
        if user and check_password_hash(user.Password_Hash, password):
            # Verificar si la cuenta está activa
            if not user.Email_Verificado or user.Estado_Cuenta != 'activo':
                flash('Tu cuenta no ha sido verificada. Por favor verifica tu correo electrónico', 'warning')
                return redirect(url_for('resend_verification'))
                
            session['user_id'] = user.ID
            session['user_email'] = user.Email
            
            # Update user connection data
            user.Ultima_Conexion = datetime.utcnow()
            user.Contador_Conexiones += 1
            db.session.commit()
            
            # Record session
            record_session(user.ID, request)
            
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        contrasena = request.form.get('password')
        confirmar_contrasena = request.form.get('confirmar_contrasena')
        genero_id = request.form.get('genero_id')
        
        # Validación de campos obligatorios (excepto teléfono temporalmente)
        if not nombre or not apellido or not email or not contrasena:
            flash('Por favor complete todos los campos obligatorios', 'danger')
            return render_template('register.html', generos=Genero.query.all())
        
        # Validación de formato de teléfono solo si se proporciona
        if telefono:
            import re
            pattern = re.compile(r'(\+?[0-9]{1,3})?[-. ]?\(?[0-9]{3}\)?[-. ]?[0-9]{3}[-. ]?[0-9]{4}')
            if not pattern.match(telefono):
                flash('El formato del número de teléfono no es válido', 'danger')
                return render_template('register.html', generos=Genero.query.all(), 
                                nombre=nombre, apellido=apellido, email=email)
        
        if contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('register.html', generos=Genero.query.all(), 
                            nombre=nombre, apellido=apellido, email=email)
        
        usuario_existente = Usuario.query.filter_by(Email=email).first()
        if usuario_existente:
            flash('El correo electrónico ya está registrado', 'danger')
            return render_template('register.html', generos=Genero.query.all(), 
                            nombre=nombre, apellido=apellido, telefono=telefono)
        
        hashed_password = generate_password_hash(contrasena)
        
        # Crear un nuevo usuario con los campos correctos
        nuevo_usuario = Usuario(
            Nombre=nombre,
            Apellido=apellido,
            Email=email,
            Telefono=telefono,
            Password_Hash=hashed_password,
            Genero_ID=genero_id if genero_id else None
        )
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        # Generar token de verificación
        token = create_verification_token(nuevo_usuario.ID)
        
        # Enviar correo de verificación
        email_sent = send_verification_email(email, token)
        
        if email_sent:
            flash('Registro exitoso! Por favor verifica tu correo electrónico para activar tu cuenta.', 'success')
        else:
            flash('Hubo un problema al enviar el correo de verificación. Por favor intenta más tarde', 'danger')
        
        return redirect(url_for('login'))
    
    return render_template('register.html', generos=Genero.query.all())

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Por favor inicia sesión primero', 'warning')
        return redirect(url_for('login'))
    
    user = Usuario.query.get(session['user_id'])
    
    # Usar el método get_saludo para obtener el saludo personalizado
    saludo = user.get_saludo()
    
    return render_template('dashboard.html', user=user, saludo=saludo)

@app.route('/verify-email/<token>')
def verify_email(token):
    # Buscar el token en la base de datos
    token_record = TokenVerificacion.query.filter_by(Token=token, Usado=False).first()
    
    if not token_record:
        flash('El enlace de verificación no es válido o ya ha sido utilizado', 'danger')
        return redirect(url_for('login'))
    
    # Verificar si el token ha expirado
    if token_record.Fecha_Expiracion < datetime.utcnow():
        flash('El enlace de verificación ha expirado. Por favor solicita uno nuevo', 'danger')
        return redirect(url_for('login'))
    
    # Actualizar el estado del usuario
    user = Usuario.query.get(token_record.Usuario_ID)
    if user:
        user.Email_Verificado = True
        user.Estado_Cuenta = 'activo'
        user.Fecha_Verificacion = datetime.utcnow()
        
        # Marcar el token como usado
        token_record.Usado = True
        
        db.session.commit()
        
        flash('¡Tu correo electrónico ha sido verificado exitosamente! Ahora puedes iniciar sesión', 'success')
    else:
        flash('Usuario no encontrado', 'danger')
    
    return redirect(url_for('login'))

@app.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Buscar el usuario por correo electrónico
        user = Usuario.query.filter_by(Email=email).first()
        
        if not user:
            flash('No se encontró ninguna cuenta con ese correo electrónico', 'danger')
            return redirect(url_for('resend_verification'))
        
        if user.Email_Verificado:
            flash('Este correo electrónico ya ha sido verificado. Puedes iniciar sesión', 'info')
            return redirect(url_for('login'))
        
        # Generar un nuevo token y enviar correo
        token = create_verification_token(user.ID)
        email_sent = send_verification_email(email, token)
        
        if email_sent:
            flash('Se ha enviado un nuevo enlace de verificación a tu correo electrónico', 'success')
        else:
            flash('Hubo un problema al enviar el correo de verificación. Por favor intenta más tarde', 'danger')
        
        return redirect(url_for('login'))
    
    return render_template('resend_verification.html')

@app.route('/generate-qr', methods=['GET', 'POST'])
def generate_qr():
    if 'user_id' not in session:
        flash('Por favor inicia sesión primero', 'warning')
        return redirect(url_for('login'))
    
    # Obtener las mascotas del usuario para el formulario
    mascotas = Mascota.query.filter_by(Dueno_ID=session['user_id']).all()
    
    if request.method == 'POST':
        lat = request.form.get('latitude')
        lng = request.form.get('longitude')
        email = session['user_email']
        mascota_id = request.form.get('mascota_id')
        
        # Get user object
        user = Usuario.query.get(session['user_id'])
        
        # Datos adicionales
        nombre_completo = f"{user.Nombre}{user.Apellido}"
        telefono = user.Telefono or "No disponible"
        
        # Obtener información de la mascota si se seleccionó
        nombre_mascota = "No seleccionada"
        if mascota_id and mascota_id != "0":
            mascota = Mascota.query.get(mascota_id)
            if mascota and mascota.Dueno_ID == user.ID:
                nombre_mascota = mascota.Nombre
        
        # Create JSON data for QR code - Incluir datos adicionales
        qr_data = {
            'lat': lat,
            'lng': lng,
            'email': email,
            'nombre': nombre_completo,
            'telefono': telefono,
            'mascota': nombre_mascota
        }
        
        # Generate QR code
        base64_img, img_bytes = generate_qrcode(json.dumps(qr_data))
        
        # Send email with QR code to user
        email_result = send_qr_email(email, img_bytes, lat, lng, user)
        
        # Send notification to admin
        admin_notified = send_admin_qr_notification(img_bytes, lat, lng, user)
        
        # Store location
        new_location = UbicacionGPS(
            Usuario_ID=session['user_id'],
            Latitud=float(lat),
            Longitud=float(lng)
        )
        db.session.add(new_location)
        db.session.commit()
        
        if email_result:
            flash('Código QR generado y enviado a tu correo', 'success')
        else:
            flash('Código QR generado pero hubo un problema al enviar el correo', 'warning')
        
        # Store QR data in session for map display
        session['qr_lat'] = lat
        session['qr_lng'] = lng
        
        return redirect(url_for('map_view'))
    
    return render_template('generate_qr.html', mascotas=mascotas)

@app.route('/scan-qr', methods=['GET', 'POST'])
def scan_qr():
    if 'user_id' not in session:
        flash('Por favor inicia sesión primero', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        qr_data = request.form.get('qr_data')
        try:
            data = json.loads(qr_data)
            # Extract all data fields
            email = data.get('email', 'No disponible')
            lat = data.get('lat', 'No disponible')
            lng = data.get('lng', 'No disponible')
            nombre = data.get('nombre', 'No disponible')
            telefono = data.get('telefono', 'No disponible')
            mascota = data.get('mascota', 'No disponible')
            
            # Notify the pet owner that their QR was scanned
            if email and '@' in email:
                owner_notified = notify_qr_scan(email, request.remote_addr)
                notification_status = "Propietario notificado" if owner_notified else "Error al notificar al propietario"
            else:
                notification_status = "Correo inválido, no se pudo notificar al propietario"
            
            # Render template with all the extracted data
            return render_template('qr_result.html', 
                                  email=email, 
                                  lat=lat, 
                                  lng=lng, 
                                  nombre=nombre,
                                  telefono=telefono, 
                                  mascota=mascota,
                                  notification_status=notification_status)
        except Exception as e:
            flash(f'Error al procesar el código QR: {str(e)}', 'danger')
            return redirect(url_for('scan_qr'))
    
    return render_template('scan_qr.html')

@app.route('/map')
def map_view():
    if 'user_id' not in session:
        flash('Por favor inicia sesión primero', 'warning')
        return redirect(url_for('login'))
    
    context = {
        'qr_lat': session.get('qr_lat'),
        'qr_lng': session.get('qr_lng'),
        'scanner_lat': session.get('scanner_lat'),
        'scanner_lng': session.get('scanner_lng')
    }
    
    return render_template('map.html', **context)

@app.route('/logout')
def logout():
    if 'session_id' in session:
        update_session_end(session['session_id'])
    
    session.clear()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('login'))

@app.route('/mascotas')
def listar_mascotas():
    if 'user_id' not in session:
        flash('Por favor inicia sesión primero', 'warning')
        return redirect(url_for('login'))
    
    # Obtener mascotas del usuario actual
    mascotas = Mascota.query.filter_by(Dueno_ID=session['user_id']).all()
    
    return render_template('mascotas.html', mascotas=mascotas)

@app.route('/mascotas/agregar', methods=['GET', 'POST'])
def agregar_mascota():
    if 'user_id' not in session:
        flash('Por favor inicia sesión primero', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        especie = request.form.get('especie')
        raza = request.form.get('raza')
        edad = request.form.get('edad')
        
        if not nombre:
            flash('El nombre de la mascota es obligatorio', 'danger')
            return render_template('add_mascota.html')
        
        # Crear nueva mascota
        nueva_mascota = Mascota(
            Nombre=nombre,
            Especie=especie,
            Raza=raza,
            Edad=edad if edad else None,
            Dueno_ID=session['user_id']
        )
        
        db.session.add(nueva_mascota)
        db.session.commit()
        
        flash('¡Mascota registrada con éxito!', 'success')
        return redirect(url_for('listar_mascotas'))
    
    return render_template('add_mascota.html')

@app.route('/mascotas/editar/<int:mascota_id>', methods=['GET', 'POST'])
def editar_mascota(mascota_id):
    if 'user_id' not in session:
        flash('Por favor inicia sesión primero', 'warning')
        return redirect(url_for('login'))
    
    mascota = Mascota.query.get_or_404(mascota_id)
    
    # Verificar que la mascota pertenece al usuario actual
    if mascota.Dueno_ID != session['user_id']:
        flash('No tienes permiso para editar esta mascota', 'danger')
        return redirect(url_for('listar_mascotas'))
    
    if request.method == 'POST':
        mascota.Nombre = request.form.get('nombre')
        mascota.Especie = request.form.get('especie')
        mascota.Raza = request.form.get('raza')
        mascota.Edad = request.form.get('edad') if request.form.get('edad') else None
        
        db.session.commit()
        
        flash('Información de la mascota actualizada correctamente', 'success')
        return redirect(url_for('listar_mascotas'))
    
    return render_template('edit_mascota.html', mascota=mascota)

@app.route('/mascotas/eliminar/<int:mascota_id>')
def eliminar_mascota(mascota_id):
    if 'user_id' not in session:
        flash('Por favor inicia sesión primero', 'warning')
        return redirect(url_for('login'))
    
    mascota = Mascota.query.get_or_404(mascota_id)
    
    # Verificar que la mascota pertenece al usuario actual
    if mascota.Dueno_ID != session['user_id']:
        flash('No tienes permiso para eliminar esta mascota', 'danger')
        return redirect(url_for('listar_mascotas'))
    
    db.session.delete(mascota)
    db.session.commit()
    
    flash('Mascota eliminada correctamente', 'success')
    return redirect(url_for('listar_mascotas'))

@app.route('/encontrado')
def mascota_encontrada():
    """
    Ruta pública para acceder a la información del QR sin estar registrado.
    Esta ruta es accesible desde cualquier aplicación de escaneo QR de terceros.
    """
    # Obtener los parámetros de la URL
    email = request.args.get('email', 'No disponible')
    lat = request.args.get('lat', 'No disponible')
    lng = request.args.get('lng', 'No disponible')
    nombre = request.args.get('nombre', 'No disponible')
    telefono = request.args.get('telefono', 'No disponible')
    mascota = request.args.get('mascota', 'No disponible')
    
    # Notificar al propietario que su QR ha sido escaneado
    notification_status = "No se pudo notificar al propietario"
    if email and '@' in email:
        try:
            owner_notified = notify_qr_scan(email, request.remote_addr)
            notification_status = "Propietario notificado" if owner_notified else "Error al notificar al propietario"
        except Exception as e:
            notification_status = f"Error al notificar: {str(e)}"
    
    # Renderizar la plantilla de resultado con los datos del QR
    return render_template('qr_result.html',
                          email=email,
                          lat=lat,
                          lng=lng,
                          nombre=nombre,
                          telefono=telefono,
                          mascota=mascota,
                          notification_status=notification_status)

if __name__ == '__main__':
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Add default genders if not exist
        if not Genero.query.first():
            generos = [
                Genero(ID=1, Descripcion="Masculino"),
                Genero(ID=2, Descripcion="Femenino"),
                Genero(ID=3, Descripcion="Otro")
            ]
            db.session.add_all(generos)
            db.session.commit()
    
    app.run(debug=True) 
import sys
import os

# Añade el directorio que contiene tu aplicación al path de Python
path = '/home/PruebasJR/mysite'
if path not in sys.path:
    sys.path.append(path)

# Configura variables de entorno
os.environ['SECRET_KEY'] = 'secretkey123456789'
os.environ['DB_USERNAME'] = 'PruebasJR'
os.environ['DB_PASSWORD'] = 'Emprendimiento2025'
os.environ['DB_HOSTNAME'] = 'PruebasJR.mysql.pythonanywhere-services.com'
os.environ['DB_NAME'] = 'PruebasJR$GeoPet'

# Importa tu aplicación
from app import app as application 
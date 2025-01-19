from app.db.config_mongo import getConexionMongo
import jwt
import os
from dotenv import load_dotenv
import bcrypt

# Cargar las variables de entorno desde un archivo .env
load_dotenv()

# Obtener la clave secreta desde las variables de entorno
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY no está configurada en las variables de entorno")

def login_user(username, password):
    """
    Autentica a un usuario y genera un token JWT si las credenciales son válidas.
    """
    db = getConexionMongo()
    user = db.users.find_one({"username": username})

    if user and bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
        token = jwt.encode({"username": username}, SECRET_KEY, algorithm="HS256")
        return {"token": token}
    else:
        return {"error": "Invalid username or password"}

def create_user(username, password):
    """
    Crea un nuevo usuario en la base de datos si no existe ya un usuario con el mismo nombre.
    """
    db = getConexionMongo()
    existing_user =  db.users.find_one({"username": username})
    if existing_user:
        raise ValueError(f"User {username} already exists")

    # Encriptar la contraseña antes de guardarla en la base de datos
    hashPassword = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    db.users.insert_one({"username": username, "password": hashPassword})
    return {"username": username}
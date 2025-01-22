from app.db.config_mongo import getConexionMongo
import jwt
import os
from dotenv import load_dotenv
import bcrypt
import math
from bson import ObjectId

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

def create_user(username, password, name=None):
    """
    Crea un nuevo usuario en la base de datos si no existe ya un usuario con el mismo nombre.
    Se incluye opcionalmente el campo 'name'.
    """
    db = getConexionMongo()
    existing_user = db.users.find_one({"username": username})
    if existing_user:
        raise ValueError(f"User {username} already exists")

    # Encriptar la contraseña antes de guardarla en la base de datos
    hashPassword = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Creamos el documento a insertar
    user_doc = {
        "username": username,
        "password": hashPassword
    }

    # Solo agregamos el campo name si viene en la llamada
    if name:
        user_doc["name"] = name

    db.users.insert_one(user_doc)

    return {"username": username, "name": name,"id":str(user_doc["_id"])}

def list_users(email_search=None, pagina=1, limite=10):
    """
    Lista usuarios con paginación y búsqueda opcional por email.
    Retorna el id (string), username y name de cada usuario.

    :param email_search: (str) Texto para filtrar usuarios cuyo email coincida (usando regex).
    :param pagina: (int) Número de página a retornar.
    :param limite: (int) Cantidad de registros por página.
    :return: dict con estructura:
        {
          "registros": [...],
          "pagina_actual": pagina,
          "paginas_restantes": 0,
          "total_registros": 0
        }
    """
    db = getConexionMongo()
    
    # Construimos la query
    query = {}
    if email_search:
        # Usamos regex para buscar coincidencias parciales (equivalente a LIKE %email_search%)
        # El '.*' antes y después permite que el término de búsqueda aparezca en cualquier parte del email
        regex_pattern = f".*{email_search}.*"
        query["username"] = {"$regex": regex_pattern, "$options": "i"}
    
    # Contar el total de documentos que cumplen la condición
    total_registros = db.users.count_documents(query)
    
    # Cálculo de paginación
    skip = (pagina - 1) * limite
    
    # Proyección: obtenemos _id, username y name. (No retornamos password)
    cursor = db.users.find(
        query,
        {"_id": 1, "username": 1, "name": 1}
    ).skip(skip).limit(limite)
    
    registros = []
    for doc in cursor:
        registros.append({
            "id": str(doc["_id"]),
            "username": doc.get("username", ""),
            "name": doc.get("name", "")
        })
    
    # Cálculo de páginas (ceil para redondear hacia arriba)
    total_paginas = math.ceil(total_registros / limite) if limite > 0 else 0


    return {
        "status":True,
        "message":"exito",
        "statusCode":200,
        "result":{
            "total":total_registros,
            "data":registros,
            "currentPage":pagina,
            "hasNextPage":total_paginas>pagina,
            "hasPreviousPage":pagina>1,
            "totalPages":total_paginas
        }
    }


def update_user_password(user_id, new_password):
    """
    Actualiza la contraseña de un usuario dado su ID.
    Se encripta la nueva contraseña antes de almacenarla.
    
    :param user_id: (str) ID del usuario en formato string (ObjectId).
    :param new_password: (str) Nueva contraseña en texto plano.
    :return: dict con información del resultado de la operación.
    """
    db = getConexionMongo()

    # Convertir string a ObjectId para la búsqueda
    obj_id = ObjectId(user_id)
    user = db.users.find_one({"_id": obj_id})

    if not user:
        raise ValueError("No se encontró un usuario con ese ID")

    # Encriptar la nueva contraseña
    hash_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Actualizar la contraseña en la base de datos
    db.users.update_one({"_id": obj_id}, {"$set": {"password": hash_password}})

    return {
        "status": "success",
        "message": "Contraseña actualizada correctamente."
    }

def update_user_email(user_id, new_email):
    """
    Actualiza el email de un usuario dado su ID, asegurando que el nuevo email sea único.
    
    :param user_id: (str) ID del usuario en formato string (ObjectId).
    :param new_email: (str) Nuevo email del usuario.
    :return: dict con información del resultado de la operación.
    """
    db = getConexionMongo()

    # Verificar si el nuevo email ya existe en otro usuario
    existing_email_user = db.users.find_one({"email": new_email})
    if existing_email_user:
        raise ValueError("El email proporcionado ya está en uso por otro usuario.")

    obj_id = ObjectId(user_id)
    user = db.users.find_one({"_id": obj_id})
    if not user:
        raise ValueError("No se encontró un usuario con ese ID")

    # Actualizar el email del usuario
    db.users.update_one({"_id": obj_id}, {"$set": {"email": new_email}})

    return {
        "status": "success",
        "message": "Email actualizado correctamente."
    }

def edit_user(user_id, username=None, name=None):
    """
    Edita el username y/o name de un usuario dado su ID.
    Si se proporciona un nuevo username, se verifica que sea único.

    :param user_id: (str) ID del usuario en formato string (ObjectId).
    :param username: (str) Nuevo username (opcional).
    :param name: (str) Nuevo nombre (opcional).
    :return: dict con información del resultado de la operación.
    """
    db = getConexionMongo()
    obj_id = ObjectId(user_id)

    # Verificar si el usuario existe
    user = db.users.find_one({"_id": obj_id})
    if not user:
        raise ValueError("No se encontró un usuario con ese ID")

    update_fields = {}
    if username:
        # Verificar que el nuevo username no esté en uso por otro usuario
        existing_user = db.users.find_one({"username": username, "_id": {"$ne": obj_id}})
        if existing_user:
            raise ValueError("El username proporcionado ya está en uso por otro usuario.")
        update_fields["username"] = username

    if name:
        update_fields["name"] = name

    if not update_fields:
        raise ValueError("No se proporcionaron campos para actualizar.")

    # Actualizar los campos proporcionados
    db.users.update_one({"_id": obj_id}, {"$set": update_fields})

    return {
        "status": "success",
        "message": "Usuario actualizado correctamente."
    }



def delete_user(user_id):
    """
    Elimina un usuario de la base de datos dado su ID.

    :param user_id: (str) ID del usuario en formato string (ObjectId).
    :return: dict con información del resultado de la operación.
    """
    db = getConexionMongo()
    obj_id = ObjectId(user_id)

    # Verificar si el usuario existe
    user = db.users.find_one({"_id": obj_id})
    if not user:
        raise ValueError("No se encontró un usuario con ese ID")

    # Eliminar el usuario
    result = db.users.delete_one({"_id": obj_id})

    if result.deleted_count == 1:
        return {
            "status": "success",
            "message": "Usuario eliminado correctamente."
        }
    else:
        return {
            "status": "error",
            "message": "No se pudo eliminar el usuario."
        }
    

def get_user(user_id):
    """
    Obtiene los detalles de un usuario dado su ID.
    Retorna el id, username y name del usuario.

    :param user_id: (str) ID del usuario en formato string (ObjectId).
    :return: dict con los detalles del usuario o un error si no se encuentra.
    """
    db = getConexionMongo()
    obj_id = ObjectId(user_id)

    user = db.users.find_one(
        {"_id": obj_id},
        {"_id": 1, "username": 1, "name": 1}
    )

    if not user:
        raise ValueError("No se encontró un usuario con ese ID")

    return {
        "id": str(user["_id"]),
        "username": user.get("username", ""),
        "name": user.get("name", "")
    }
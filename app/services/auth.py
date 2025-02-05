import os
import random
import string
import smtplib
from email.mime.text import MIMEText

from dotenv import load_dotenv

from app.db.config_mongo import getConexionMongo
from app.repositories.user.user import (
    login_user,
    create_user,
    list_users,
    update_user_email,
    update_user_password,
    edit_user as repo_edit_user,
    delete_user as repo_delete_user,
    get_user as repo_get_user
)
from bson import ObjectId

# Cargar variables de entorno
load_dotenv()

# Opcional: Variables para SMTP (ajusta según tu entorno)
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = os.getenv("SMTP_PORT", "587")
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")


class UserService:
    def login(self, username: str, password: str) -> dict:
        """
        Autentica a un usuario y genera un token JWT si las credenciales son válidas.

        :param username: Nombre de usuario
        :param password: Contraseña
        :return: Diccionario con el token JWT o un mensaje de error
        """
        return login_user(username, password)

    def create_user(self, username: str,name:str) -> dict:
        """
        Crea un nuevo usuario en la base de datos si no existe ya un usuario con el mismo nombre.

        :param username: Nombre de usuario
        :param password: Contraseña
        :param name: Contraseña
        :return: Diccionario con un mensaje de éxito o error
        """
        password = self._generate_random_password(6)
         
        #validar que no haya un usuario con el mismo nombre
        db = getConexionMongo()
        user = db.users.find_one({"username": username})
        if user:
            return {"status": "error", "message": "Ya existe un usuario con ese email."}
        self._send_email("username", password)   
        return create_user(username, password,name)

    def list_all_users(self, email_search: str = None, pagina: int = 1, limite: int = 10) -> dict:
        """
        Lista usuarios con paginación y búsqueda opcional por email.

        :param email_search: Filtro opcional para buscar por email
        :param pagina: Número de página
        :param limite: Cantidad de registros por página
        :return: Diccionario con la estructura:
                 {
                     "registros": [...],
                     "pagina_actual": pagina,
                     "paginas_restantes": ...,
                     "total_registros": ...
                 }
        """
        return list_users(email_search, pagina, limite)

    def update_email(self, user_id: str, new_email: str) -> dict:
        """
        Actualiza el email de un usuario dado su ID, asegurando que el nuevo email sea único.

        :param user_id: ID del usuario (cadena en formato ObjectId)
        :param new_email: Nuevo email a asignar
        :return: Diccionario con el resultado de la operación
        """
        return update_user_email(user_id, new_email)

    def send_new_password(self, user_id: str) -> dict:
        """
        Genera automáticamente una nueva contraseña de 6 caracteres alfanuméricos, 
        la actualiza para el usuario y envía un correo con esa nueva contraseña.

        :param user_id: ID del usuario (cadena en formato ObjectId)
        :return: Diccionario con el resultado de la operación
        """
        db = getConexionMongo()

        # Verificar si el usuario existe y obtener su email
        user_obj_id = ObjectId(user_id)
        user = db.users.find_one({"_id": user_obj_id}, {"username": 1})
        if not user:
            return {"status": "error", "message": "Usuario no encontrado."}
      

        new_password = self._generate_random_password(6)
   
        
        # Actualizar la contraseña en la base de datos
        update_user_password(user_id, new_password)
        print(user)
        # Enviar el correo con la nueva contraseña
        self._send_email(user["username"], new_password)

        return {
            "status": "success",
            "message": "Se ha generado y enviado una nueva contraseña al correo."
        }
    def edit_user(self, user_id: str, username: str = None, name: str = None) -> dict:
        """
        Edita el username y/o name de un usuario dado su ID.

        :param user_id: ID del usuario (cadena en formato ObjectId)
        :param username: Nuevo username (opcional)
        :param name: Nuevo nombre (opcional)
        :return: Diccionario con el resultado de la operación
        """
        try:
            result = repo_edit_user(user_id, username, name)
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def delete_user(self, user_id: str) -> dict:
        """
        Elimina un usuario dado su ID.

        :param user_id: ID del usuario (cadena en formato ObjectId)
        :return: Diccionario con el resultado de la operación
        """
        try:
            result = repo_delete_user(user_id)
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_user(self, user_id: str) -> dict:
        """
        Obtiene los detalles de un usuario dado su ID.

        :param user_id: ID del usuario (cadena en formato ObjectId)
        :return: Diccionario con los detalles del usuario o un error si no se encuentra
        """
        try:
            user = repo_get_user(user_id)
            return {
                "status": "success",
                "data": user
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _generate_random_password(self, length: int = 6) -> str:
        """
        Genera una contraseña aleatoria de longitud `length` con caracteres alfanuméricos.

        :param length: longitud de la contraseña
        :return: contraseña generada
        """
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def _generate_random_password(self, length: int = 6) -> str:
        """
        Genera una contraseña aleatoria de longitud `length` con caracteres alfanuméricos.

        :param length: longitud de la contraseña
        :return: contraseña generada
        """
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def _send_email(self, to_email: str, new_password: str):
        """
        Envía un correo electrónico con la nueva contraseña.
        Ajusta este método según tu servicio/mecanismo de envío de email preferido.

        :param to_email: Email de destino
        :param new_password: Contraseña recién generada para el usuario
        """
        subject = "Tu nueva contraseña"
        body = f"Hola,\n\nTu nueva contraseña es: {new_password}\n\nSaludos,\nEquipo de Soporte"

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER if SMTP_USER else "no-reply@example.com"
        msg["To"] = to_email

        try:
            with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT)) as server:
                server.starttls()  # Inicia TLS si el puerto lo requiere
                if SMTP_USER and SMTP_PASS:
                    server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
        except Exception as e:
            # Manejar error de envío de correo
            print(f"[Error] No se pudo enviar el email: {e}")

from app.db.config_mongo import getConexionMongo
from app.repositories.user.user import login_user, create_user

class UserService:
    def login(self, username: str, password: str) -> dict:
        """
        Autentica a un usuario y genera un token JWT si las credenciales son válidas.

        :param username: Nombre de usuario
        :param password: Contraseña
        :return: Diccionario con el token JWT o un mensaje de error
        """
        return login_user(username, password)

    def create_user(self, username: str, password: str) -> dict:
        """
        Crea un nuevo usuario en la base de datos si no existe ya un usuario con el mismo nombre.

        :param username: Nombre de usuario
        :param password: Contraseña
        :return: Diccionario con un mensaje de éxito o error
        """
        return create_user(username, password)

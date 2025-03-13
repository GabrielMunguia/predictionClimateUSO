from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel,EmailStr
from typing import Optional

from app.services.auth import UserService

router = APIRouter(prefix="/api/auth")

# Crear una instancia del servicio
user_service = UserService()

# Modelos de Pydantic
class EmailRequest(BaseModel):
    email: str
class RegisterUserRequest(BaseModel):
    username: EmailStr
   
    name: Optional[str] = None  # Campo opcional
class LoginRequest(BaseModel):
    username: EmailStr
    password: str

class UpdateUserRequest(BaseModel):
    username: Optional[EmailStr] = None
    name: Optional[str] = None

class UpdateEmailRequest(BaseModel):
    new_email: str

# Endpoints existentes

@router.post("/register")
def register_user(request: RegisterUserRequest):
    try:
        user = user_service.create_user(request.username, request.name)
        return {"message": "User created successfully", "user": user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login_user(request: LoginRequest):
    try:
        user = user_service.login(request.username, request.password)
        return {"message": "User logged in successfully", "user": user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Nuevos Endpoints

@router.get("/users")
def list_users_endpoint(
    email_search: Optional[str] = None,
    page: int = 1,
    limit: int = 10
):
    """
    Lista usuarios con paginación y búsqueda opcional por email.
    """
    try:
        result = user_service.list_all_users(email_search, page, limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/users/send-new-password")
def send_new_password_endpoint(request: EmailRequest):
    """
    Genera y envía una nueva contraseña a un usuario específico.
    """
    try:
        result = user_service.send_new_password(request.email)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.put("/users/{user_id}")
def edit_user_endpoint(user_id: str, request: UpdateUserRequest):
    """
    Edita el username y/o name de un usuario.
    """
    try:
        #validar que si se envia el username sea un email valido
        
        result = user_service.edit_user(user_id, request.username, request.name)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/users/{user_id}")
def delete_user_endpoint(user_id: str):
    """
    Elimina un usuario dado su ID.
    """
    try:
        result = user_service.delete_user(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/users/{user_id}")
def get_user_endpoint(user_id: str):
    """
    Obtiene los detalles de un usuario dado su ID.
    """
    try:
        result = user_service.get_user(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.services.auth import create_user, UserService
from app.utils.model import traningModel
import os
import tempfile

router = APIRouter(prefix="/api/auth")

# Crear una instancia del servicio
user_service = UserService()

# Modelo para la solicitud de registro
class RegisterUserRequest(BaseModel):
    username: str
    password: str

@router.post("/register")
def register_user(request: RegisterUserRequest):
    try:
        user =   create_user(request.username, request.password)
        return {"message": "User created successfully", "user": user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login_user(request: RegisterUserRequest):
    try:
        user = user_service.login(request.username, request.password)
        return {"message": "User logged in successfully", "user": user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    


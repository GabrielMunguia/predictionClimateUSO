from fastapi import FastAPI
from app.routes.traning_model import router  # Asegúrate de importar el router correctamente
from app.routes.auth import router as routerAuth  
from app.routes.predict import router as routerPredict
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI(title='Api de clima', version='0.1')
# Incluir las rutas del router
app.include_router(router)
app.include_router(routerAuth)
app.include_router(routerPredict)
#//activar cors

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite el acceso desde cualquier origen
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos
    allow_headers=["*"],  # Permite todas las cabeceras
)
app.mount("/scripts", StaticFiles(directory="public/scripts"), name="scripts")

@app.get("/")
def read_root():
    return FileResponse("public/index.html")
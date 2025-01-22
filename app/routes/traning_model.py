from fastapi import APIRouter, HTTPException, UploadFile, File,Query,Depends
from app.services.process_csv import CSVProcessorService
from app.utils.model import traningModel
import os
import tempfile

router = APIRouter(prefix="/api/traning")

# Crear una instancia del servicio
product_service = CSVProcessorService()

@router.post("/")
async def insert_data(file: UploadFile = File(...)):
    try:
        # Obtener el nombre del archivo y su extensión
        filename = file.filename
        _, extension = os.path.splitext(filename)  # Separar el nombre y la extensión

        # Verificar que el archivo sea un CSV
        if extension.lower() != '.csv':
            raise HTTPException(status_code=400, detail="El archivo debe ser un CSV")
        
        # Crear un archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name  # Ruta del archivo temporal

        # Procesar el archivo con el servicio
        try:
          await product_service.process_csv(temp_file_path) 
          traningModel()
        except Exception as e:
            raise HTTPException(status_code=500, detail=e.args[0])
        
        # Eliminar el archivo temporal después de procesarlo
        os.remove(temp_file_path)

        return {"messagex": "CSV processed successfully", "status": "ok"}

    except Exception as e:
        #print erro
        print(f"Hubo un error {str(e)} ")
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/list")
async def list_data(
    fecha_inicio: str = Query(None, description="Start date for filtering in 'YYYY-MM-DD HH:MM:SS' format"),
    fecha_fin: str = Query(None, description="End date for filtering in 'YYYY-MM-DD HH:MM:SS' format"),
    orden_fecha: str = Query(None, description="Order by date ('asc' or 'desc')"),
    search: str = Query(None, description="Search term to filter across all fields"),
    page: int = Query(1, ge=1, description="Page number for pagination (default 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Page size for pagination (default 10, max 100)"),
    product_service: CSVProcessorService = Depends()
):
   
    try:
        # Call the service to fetch the records and return the result
        return await product_service.listar_registros(
            fecha_inicio, fecha_fin, orden_fecha, search, page, page_size
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print("Error listing records:", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/")

async def training():
    try:
        traningModel()
        return {"message": "Model trained successfully", "status": "ok"}
    except Exception as e:
        print(f"Hubo un error {str(e)} ")
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))
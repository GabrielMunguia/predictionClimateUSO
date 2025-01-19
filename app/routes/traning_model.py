from fastapi import APIRouter, HTTPException, UploadFile, File
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
        print("Hubo un error")
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))

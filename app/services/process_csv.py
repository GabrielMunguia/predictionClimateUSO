from app.utils.parser_csv import parsear_csv
import pandas as pd

from app.repositories.climate_history.climate_history import insertar_datos_clima_db
class CSVProcessorService:
      async def process_csv(self, archivo_entrada):
      
        # Pasar la ruta del archivo temporal a insertar_datos_clima_db
        await insertar_datos_clima_db(archivo_entrada)
        # si es verdad que el archivo se parseo correctamente devolver un json con el mensaje y status
        return True
      
    

from app.utils.parser_csv import parsear_csv
import pandas as pd

from app.repositories.climate_history.climate_history import insertar_datos_clima_db,listar_registros,eliminar_registros
class CSVProcessorService:
      async def process_csv(self, archivo_entrada):
      
        # Pasar la ruta del archivo temporal a insertar_datos_clima_db
        await insertar_datos_clima_db(archivo_entrada)
        # si es verdad que el archivo se parseo correctamente devolver un json con el mensaje y status
        return True
      def listar_registros(self, fecha_inicio=None, fecha_fin=None, orden_fecha=None, search=None, page=1, page_size=10):
        """
        Llama a la función listar_registros de la base de datos con soporte para paginación.

        :param fecha_inicio: Fecha de inicio para filtrar (opcional).
        :param fecha_fin: Fecha de finalización para filtrar (opcional).
        :param orden_fecha: Orden de la fecha ('asc' para ascendente o 'desc' para descendente).
        :param search: Término de búsqueda para filtrar en cualquier campo (opcional).
        :param page: Número de página para la paginación.
        :param page_size: Tamaño de página para la paginación.
        :return: Diccionario con registros, página actual, páginas restantes y total de registros.
        """
        return listar_registros(fecha_inicio, fecha_fin, orden_fecha, search, page, page_size)
      
      ##Eliminar registros por rango de fechas
      def eliminar(self, fecha_inicio, fecha_fin):
        """
        Elimina registros de la base de datos en un rango de fechas.

        :param fecha_inicio: Fecha de inicio para filtrar.
        :param fecha_fin: Fecha de finalización para filtrar.
        :return: True si se eliminaron registros, False si no se eliminaron.
        """
        return eliminar_registros(fecha_inicio, fecha_fin)
      
import pandas as pd

from app.utils.parser_csv import parsear_csv
from app.db.config_mongo import getConexionMongo
from math import ceil
def validar_valores(valor):
    # Intentar validar si es una fecha
    
    try:
        fecha = pd.to_datetime(valor,
         format='%Y-%m-%d %H:%M:%S', errors='coerce')
        if fecha and not pd.isna(fecha):
            return fecha  # Retornar como objeto de fecha si es válido
    except Exception:
        print(f"ocurrio un erro! ")
        pass  # Si no es fecha, continuar con el resto de validaciones

    # Validar si el valor es NaN
    if pd.isna(valor) or valor in ['', None, 'NaN', 'nan']:
        return None

    # Manejar cadenas con comas como separadores decimales
    if isinstance(valor, str):
        # Reemplazar separadores de miles y decimales
        valor = valor.replace('.', '').replace(',', '.').strip()

    # Intentar convertir el valor a un número flotante
    try:
        return float(valor)
    except (ValueError, TypeError):
        print(f"ocurrio un erro! {ValueError}")
        # Si no es un número válido, devolver None
        return None
# Función para insertar los datos en MongoDB
async def insertar_datos_clima_db(archivo_entrada):
    # Llamada a la función de parseo
    df_parseado = parsear_csv(archivo_entrada)

    # Conectar a MongoDB
    db = getConexionMongo()

    # Acceder a la colección donde se insertarán los datos
    collection = db['history2']

    # Convertir el DataFrame a un formato adecuado para MongoDB (lista de diccionarios)
    data = []
    validos = 0
    invalidos = 0

    # Lista de campos requeridos para el modelo
    campos_requeridos = [
        'temperatura',                    # Temperatura (°C)
        'humedad',                        # Humedad (%)
        'presion_atmosferica',            # Presión atmosférica (hPa)
        'radiacion_solar',                # Radiación solar (W/m²)
        'lluvia',                          # Lluvia (mm)
   
    ]

    for index, row in df_parseado.iterrows():
        try:
            # Crear el documento directamente desde las filas del DataFrame parseado
            document = {col: validar_valores(row[col]) for col in df_parseado.columns}

            # Verificar si todos los campos requeridos están presentes y válidos
            if document['fecha'] is not None and all(document[campo] is not None for campo in campos_requeridos):
                data.append(document)
                validos += 1
            else:
                invalidos += 1
                #print(f"Documento inválido: {document}")
                #for campo in campos_requeridos:
                    #if document[campo] is None:
                    #    print(row)
                     #   print(f" - Campo requerido ausente o inválido: {campo} => {row[campo]}")
        except Exception as e:
            # Manejar errores en el procesamiento de filas
            invalidos += 1
           # print(f"Error al procesar la fila {index}: {e}")

    # Imprimir el resumen de validaciones
    print(f"Documentos válidos: {validos}")
    print(f"Documentos inválidos: {invalidos}")

    # Insertar documentos válidos en MongoDB
    if data:
        collection.insert_many(data)
        print(f"{validos} documentos insertados correctamente.")
    else:
        print("No hay documentos válidos para insertar.")

    return True
import pandas as pd
from app.db.config_mongo import getConexionMongo
from math import ceil
from bson import ObjectId


async def listar_registros(fecha_inicio=None, fecha_fin=None, orden_fecha=None, search=None, pagina: int = 1, tamano_pagina: int = 10):
    """
    Lista registros desde MongoDB con filtros, orden y paginación.

    :param fecha_inicio: Fecha de inicio para filtrar (opcional).
    :param fecha_fin: Fecha de finalización para filtrar (opcional).
    :param orden_fecha: Orden de la fecha ('asc' o 'desc', opcional).
    :param search: Término de búsqueda (opcional).
    :param pagina: Número de página (por defecto 1).
    :param tamano_pagina: Tamaño de la página (por defecto 10).
    :return: Diccionario con los registros y metadatos de paginación.
    """
    db = getConexionMongo()
    collection = db['history2']

    # Construir la consulta de filtro
    query = {}
    if fecha_inicio:
        query["fecha"] = {"$gte": pd.to_datetime(fecha_inicio)}
    if fecha_fin:
        query["fecha"] = query.get("fecha", {})
        query["fecha"]["$lte"] = pd.to_datetime(fecha_fin)

    if search:
        query["fecha"] = {"$search": search}

    print("Consulta generada:", query)  # Depuración

    # Contar documentos
    total_registros = collection.count_documents(query)
    if total_registros == 0:
        return {
            "registros": [],
            "pagina_actual": pagina,
            "paginas_restantes": 0,
            "total_registros": 0,
        }

    # Orden y paginación
    sort_order = [("fecha", -1)]
    salto = (pagina - 1) * tamano_pagina

    # Consulta con paginación
    cursor = collection.find(query)
    
    cursor = cursor.sort(sort_order)
    cursor = cursor.skip(salto).limit(tamano_pagina)

    # Convertir registros a lista y procesar ObjectId
    registros = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])  # Convertir ObjectId a cadena
        registros.append(doc)

    # Calcular páginas restantes
    total_paginas = ceil(total_registros / tamano_pagina)
    paginas_restantes = max(total_paginas - pagina, 0)


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


##Eliminar registros por rango de fechas
async def eliminar_registros(fecha_inicio=None, fecha_fin=None):
    """
    Elimina registros desde MongoDB con filtros de fecha.

    :param fecha_inicio: Fecha de inicio para filtrar (opcional).
    :param fecha_fin: Fecha de finalización para filtrar (opcional).
    :return: Número de registros eliminados.
    """
    db = getConexionMongo()
    collection = db['history2']

    # Construir la consulta de filtro
    query = {}
    if fecha_inicio:
        query["fecha"] = {"$gte": pd.to_datetime(fecha_inicio)}
    if fecha_fin:
        query["fecha"] = query.get("fecha", {})
        query["fecha"]["$lte"] = pd.to_datetime(fecha_fin)

    print("Consulta generada:", query)  # Depuración

    # Eliminar documentos
    resultado = collection.delete_many(query)

    return {
        "status":True,
        "message":"exito",
        "statusCode":200,
        "result":{
            "deletedCount":resultado.deleted_count
        }
    }

   


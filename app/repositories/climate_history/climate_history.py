import pandas as pd

from app.utils.parser_csv import parsear_csv
from app.db.config_mongo import getConexionMongo

def validar_valores(valor):
    # Intentar validar si es una fecha
    try:
        fecha = pd.to_datetime(valor, format='%Y-%m-%d %H:%M:%S', errors='coerce')
        if fecha and not pd.isna(fecha):
            return fecha  # Retornar como objeto de fecha si es válido
    except Exception:
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
                print(f"Documento inválido: {document}")
                for campo in campos_requeridos:
                    if document[campo] is None:
                        print(f" - Campo requerido ausente o inválido: {campo} => {row[campo]}")
        except Exception as e:
            # Manejar errores en el procesamiento de filas
            invalidos += 1
            print(f"Error al procesar la fila {index}: {e}")

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


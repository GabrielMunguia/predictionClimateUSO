import pandas as pd
import chardet
def detectar_codificacion(archivo):
    with open(archivo, 'rb') as f:  # Abrir el archivo en modo binario
        raw_data = f.read()  # Leer el contenido
        resultado = chardet.detect(raw_data)  # Detectar la codificación
        return  resultado

# Llama a la función con tu archivo CSV

def parsear_csv(archivo_entrada):
    # Nuevos nombres para las columnas, según el formato de tu tabla
    nuevos_nombres = [
    'fecha',                         # Fecha (America/El_Salvador)
    'temperatura_interior',           # Temperatura interior (°C)
    'temperatura',                    # Temperatura (°C)
    'sensacion_termica',              # Sensación térmica (°C)
    'punto_rocío_interior',           # Punto de rocío interior (°C)
    'punto_rocío',                    # Punto de rocío (°C)
    'indice_calor_interior',          # Índice de calor interior (°C)
    'indice_calor',                   # Índice de calor (°C)
    'humedad_interior',               # Humedad interior (%)
    'humedad',                        # Humedad (%)
    'rafaga_maxima_viento',           # Ráfaga máxima de viento (m/s)
    'velocidad_media_viento',         # Velocidad media del viento (m/s)
    'direccion_media_viento',         # Dirección media del viento (°)
    'presion_atmosferica',            # Presión atmosférica (hPa)
    'lluvia',                         # Lluvia (mm)
    'evapotranspiracion',             # Evapotranspiración (mm)
    'intensidad_lluvia',              # Intensidad de lluvia (mm/h)
    'radiacion_solar',                # Radiación solar (W/m²)
    'indice_uv'                       # Índice UV
    ]
    
    # Leer el archivo CSV especificando el delimitador correcto
    encoding=detectar_codificacion(archivo_entrada).get('encoding')
    print(encoding)
    df = pd.read_csv(archivo_entrada, encoding=encoding, delimiter=';', on_bad_lines='skip')
    print(df.head())
    print(f'Número de columnas en el CSV: {df.shape[1]}')
    

    if df.shape[1] > len(nuevos_nombres):
        df = df.iloc[:, :-1]  # Elimina la última columna si tiene una columna extra
    # Asignar los nuevos nombres de columna
    df.columns = nuevos_nombres
    print(df.head())
    # Guardar el DataFrame con los nuevos nombres de las columnas
  
    
    # Devolver el DataFrame parseado
    return df


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from datetime import datetime
import pymongo
from app.utils.model import traningModel
def getConexionMongo():
    host = "localhost"
    puerto = 27017
    base_de_datos = "tesis"
    
    cliente = pymongo.MongoClient(host, puerto)
    db = cliente[base_de_datos]
    return db
# Configurar Selenium
def syncDataWeather():
  print("holaxxxxxxxxxxxxxx")
  options = webdriver.ChromeOptions()
 # options.add_argument("--headless")  # Eliminar esta línea si quieres ver el proceso
  driver = webdriver.Chrome(options=options)
  
  # URL de Weathercloud
  BASE_URL = "https://app.weathercloud.net/"
  
  # Credenciales
  USERNAME = "iot@usonsonate.edu.sv"
  PASSWORD = "Cuz07108!"
  db = getConexionMongo()
  collection = db['history2']
  
  # Dispositivos a seleccionar
  devices = {"USO": "6878803353", "SAN MACERLINO": "4280243186"}
  
  # Campos requeridos para validar datos
  campos_requeridos = [
      'temperatura',                    # Temperatura (°C)
      'humedad',                        # Humedad (%)
      'presion_atmosferica',            # Presión atmosférica (hPa)
      'radiacion_solar',                # Radiación solar (W/m²)
      'lluvia',    
      "fecha"                     # Lluvia (mm)
  ]
  
  # Definir nombres de columnas extraídas de la tabla
  # columns = ["fecha", "temperatura_interior", "temperatura", "sensacion_termica", "punto_rocío_interior",
  #            "punto_rocío", "indice_calor_interior", "indice_calor", "humedad_interior", "humedad",
  #            "rafaga_maxima_viento", "velocidad_media_viento", "direccion_media_viento", "presion_atmosferica",
  #            "lluvia", "evapotranspiracion", "intensidad_lluvia", "radiacion_solar", "indice_uv"]
  columns = ["fecha","temperatura","humedad","presion_atmosferica","velocidad_media_viento","rafaga_maxima_viento","direccion_media_viento","lluvia","intensidad_lluvia","radiacion_solar","evapotranspiracion","indice_uv"]
  
  # 1️⃣ Abrir la página principal
  driver.get(BASE_URL)
  time.sleep(2)  # Espera a que cargue la página
  
  # 2️⃣ Hacer clic en el botón "Sign in" para abrir el modal
  sign_in_button = driver.find_element(By.CSS_SELECTOR, "a.btn.btn-primary[href='#login-modal']")
  sign_in_button.click()
  time.sleep(2)  # Esperar que el modal se abra
  
  # 3️⃣ Ingresar usuario y contraseña en el modal
  username_input = driver.find_element(By.ID, "LoginForm_entity")
  password_input = driver.find_element(By.ID, "LoginForm_password")
  
  username_input.send_keys(USERNAME)
  password_input.send_keys(PASSWORD)
  
  # 4️⃣ Hacer clic en el botón "Sign in"
  login_button = driver.find_element(By.NAME, "yt0")
  login_button.click()
  time.sleep(5)  # Esperar a que se complete el inicio de sesión
  
  for device_name, device_value in devices.items():
      # 5️⃣ Ir a la página de datos
      DATA_URL = "https://app.weathercloud.net/reports"
      driver.get(DATA_URL)
      time.sleep(5)  # Esperar que la página cargue
  
      # 6️⃣ Seleccionar el dispositivo
      device_select = Select(driver.find_element(By.ID, "report-select-device"))
      device_select.select_by_value(device_value)
      print(f"✅ Dispositivo seleccionado: {device_name}")
      time.sleep(3)
  
      # 7️⃣ Seleccionar el día actual en el selector de fechas
      current_day = str(datetime.now().day)  # Obtener el día actual como string
  
      # Buscar el select
      select_element = driver.find_element(By.ID, "report-select-day")
      dropdown = Select(select_element)
  
      # Obtener todas las opciones del select
      options = [option.get_attribute("value") for option in dropdown.options]
      print("Opciones disponibles en el select:", options)
  
      # Verificar si el día actual está en la lista de valores disponibles
      if current_day in options:
          dropdown.select_by_value(current_day)
          print(f"✅ Seleccionado el día {current_day}")
      else:
          print(f"⚠️ El día {current_day} no está disponible en el selector. Seleccionando 'Mes entero'.")
          dropdown.select_by_value("0")  # Seleccionar "Mes entero" si el día no está disponible
  
      time.sleep(3)  # Esperar que el cambio se aplique
  
      # 8️⃣ Hacer clic en el botón con id="report-button-view"
      report_button = driver.find_element(By.ID, "report-button-view")
      report_button.click()
  
      # 9️⃣ Esperar a que la tabla se cargue completamente
      try:
          WebDriverWait(driver, 10).until(
              EC.presence_of_element_located((By.CSS_SELECTOR, "#report-modal-table-body tr"))
          )
      except Exception as e:
          print(f"⚠️ La tabla no se cargó correctamente para {device_name}. Intenta nuevamente.")
          continue
      
      time.sleep(3)
  
      # 🔟 Extraer datos de la tabla
      rows = driver.find_elements(By.CSS_SELECTOR, "#report-modal-table-body tr")
      data = []
  
      for row in rows:
       cols = row.find_elements(By.TAG_NAME, "td")
       row_data = [col.text.strip() if col.text.strip() else None for col in cols]
  
       print(f"Antes de convertir: {row_data}")  # 🔍 Ver valores antes de convertir
       if len(row_data) != len(columns):
        print(f"⚠️ Desajuste de columnas: Se esperaban {len(columns)} columnas, pero se encontraron {len(row_data)}")
        continue  # Saltar esta fila si no coincide la cantidad de columnas
      
       parsed_row = {
        columns[i]: value if i == 0 else (float(value) if value and value.replace('.', '', 1).isdigit() else None)
        for i, value in enumerate(row_data)
       }
  
       print(f"Después de convertir: {parsed_row}")  # 🔍 Ver valores después de convertir
  
       if all(parsed_row.get(campo) is not None for campo in campos_requeridos): 
           parsed_row['fecha'] = datetime.strptime(f"{datetime.now().year}-{datetime.now().month:02d}-{current_day} {parsed_row['fecha']}:00", "%Y-%m-%d %H:%M:%S")
           parsed_row['dispositivo'] = device_name
           data.append(parsed_row)
       else:
          print(f"❌ Registro no válido, faltan campos requeridos o tienen valores vacíos: {parsed_row}")
  
  
      # Guardar en MongoDB si hay datos válidos
      if data:
          collection.insert_many(data)
          print(f"✅ {len(data)} registros guardados en MongoDB para {device_name}")
  
      # Guardar en un archivo CSV
      csv_filename = f"weather_data_{device_name.replace(' ', '_')}.csv"
    #  pd.DataFrame(data).to_csv(csv_filename, index=False)
      traningModel()
      print(f"✅ Datos guardados en {csv_filename}")
  
  # Cerrar el navegador
  driver.quit()
  
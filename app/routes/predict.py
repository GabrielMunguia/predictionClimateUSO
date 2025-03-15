import os
import pymongo
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import joblib
import numpy as np
from datetime import datetime, timedelta
import json
from cachetools import TTLCache  # Importar TTLCache
router = APIRouter(prefix="/api/predict")

model_reg = None
model_clf = None

# Conectar a MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["tesis"]
collection = db["history2"]

# Inicializar el caché 
cache = TTLCache(maxsize=1, ttl=86400)  # 86400 segundos = 1 día
cache_predictions = TTLCache(maxsize=1, ttl=3600)



def load_models():
    global model_reg, model_clf
    try:
        root_dir = os.getcwd()
        model_reg = joblib.load(os.path.join(root_dir, "modelo_clima_regresion.pkl"))
        model_clf = joblib.load(os.path.join(root_dir, "modelo_clima_clasificacion.pkl"))
        print("Modelos cargados (serie de tiempo).")
    except Exception as e:
        print(f"Error al cargar modelos: {e}")

load_models()

@router.get("/")
async def predecir_7_dias():
    try:

        dataOrigin=''
        if model_reg is None or model_clf is None:
            raise ValueError("Los modelos no están cargados.")
            

        # 1. Obtener los últimos 100 registros desde MongoDB
        cache_key = "last_1000_records"
        
        if cache_key in cache:
            last_1000_records = cache[cache_key]
            dataOrigin="Datos obtenidos del caché."
        else:
            last_1000_records = list(collection.find().sort("fecha", -1).limit(1000))
            if not last_1000_records:
                raise HTTPException(status_code=500, detail="No hay suficientes registros en la base de datos.")
            cache[cache_key] = last_1000_records
            dataOrigin="Datos obtenidos de la base de datos y almacenados en el caché."
        
       

        # Convertir a DataFrame y ordenar por fecha
        df_history = pd.DataFrame(last_1000_records)
        df_history.sort_values(by="fecha", inplace=True)

        predictions = []
        for record in last_1000_records:
            record["_id"] = str(record["_id"])
        test = last_1000_records  

 # Generar clave para el caché de predicciones
        predictions_cache_key = "prediccitions"
        if predictions_cache_key in cache_predictions:
            predictions = cache_predictions[predictions_cache_key]
            dataOrigin+='predictiones '
            response_data = {"predicciones": predictions, "dataOrigin":dataOrigin}
            return JSONResponse(content=json.loads(json.dumps(response_data, default=str)))

        for i in range(7):
            pred_day = datetime.now() + timedelta(days=i)
            day_of_year = pred_day.timetuple().tm_yday

            sin_day = np.sin(2 * np.pi * day_of_year / 365.0)
            cos_day = np.cos(2 * np.pi * day_of_year / 365.0)

            # Crear los lags necesarios
            lagged_data = {}
            for lag in range(1, 101):
                for col in ["temperatura", "humedad", "presion_atmosferica", "radiacion_solar", "lluvia"]:
                    lagged_data[f"{col}_lag{lag}"] = df_history[col].shift(lag).iloc[-1]

            # Crear DataFrames de entrada
            X_reg_input = pd.DataFrame([lagged_data], columns=[f"{col}_lag{lag}" for lag in range(1, 101) for col in ["temperatura", "humedad", "presion_atmosferica", "radiacion_solar"]])
            X_reg_input["sin_dayofyear"] = sin_day
            X_reg_input["cos_dayofyear"] = cos_day

            X_clf_input = X_reg_input.copy()
            X_clf_input[[f"lluvia_lag{lag}" for lag in range(1, 101)]] = pd.DataFrame([lagged_data], columns=[f"lluvia_lag{lag}" for lag in range(1, 101)])

            # 2. Realizar predicciones
            reg_output = model_reg.predict(X_reg_input)[0]
            clf_proba = model_clf.predict_proba(X_clf_input)[0][1]

            temp_d, hum_d, pres_d, rad_d = reg_output

            pred = {
                "fecha": pred_day.strftime("%Y-%m-%d"),
                "temperatura_predicha": f"{temp_d:.2f} °C",
                "humedad_predicha": f"{hum_d:.2f} %",
                "presion_predicha": f"{pres_d:.2f} hPa",
                "radiacion_predicha": f"{rad_d:.2f} W/m²",
                "probabilidad_lluvia": f"{clf_proba * 100:.2f} %"
            }

            predictions.append(pred)

            # 3. Guardar la predicción en la base de datos (opcional)
            collection.update_one(
                {"fecha": pred_day},
                {"$set": pred},
                upsert=True
            )

            # 4. Actualizar el dataframe de historial para la siguiente iteración
            new_row = {
                "fecha": pred_day,
                "temperatura": temp_d,
                "humedad": hum_d,
                "presion_atmosferica": pres_d,
                "radiacion_solar": rad_d,
                "lluvia": clf_proba
            }
            df_history = pd.concat([df_history, pd.DataFrame([new_row])], ignore_index=True)
            df_history = df_history.tail(100)
        response_data = {"predicciones": predictions, "dataOrigin":dataOrigin}
        cache_predictions[predictions_cache_key] = predictions
        return JSONResponse(content=json.loads(json.dumps(response_data, default=str)))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
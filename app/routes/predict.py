import os
import pymongo
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import joblib
import numpy as np
from datetime import datetime, timedelta
import json
from cachetools import TTLCache
router = APIRouter(prefix="/api/predict")

model_reg = None
model_clf = None
reg_columns = None
clf_columns = None

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["tesis"]
collection = db["history2"]

cache = TTLCache(maxsize=1, ttl=86400) #24 horas
cache_predictions = TTLCache(maxsize=1, ttl=3600)#1Hora

def load_models():
    global model_reg, model_clf, reg_columns, clf_columns
    try:
        root_dir = os.getcwd()
        model_reg = joblib.load(os.path.join(root_dir, "modelo_clima_regresion.pkl"))
        model_clf = joblib.load(os.path.join(root_dir, "modelo_clima_clasificacion.pkl"))
        reg_columns = model_reg.estimators_[0].feature_names_in_.tolist()
        clf_columns = model_clf.feature_names_in_.tolist()
        print("Modelos y orden de columnas cargados (serie de tiempo).")
    except Exception as e:
        print(f"Error al cargar modelos: {e}")

load_models()

@router.get("/")
async def predecir_7_dias():
    try:
        dataOrigin = ''
        if model_reg is None or model_clf is None:
            raise ValueError("Los modelos no están cargados.")

        cache_key = "last_1000_records"
        if cache_key in cache:
            last_1000_records = cache[cache_key]
            dataOrigin = "Datos obtenidos del caché."
        else:
            last_1000_records = list(collection.find().sort("fecha", -1).limit(1000))
            if not last_1000_records:
                raise HTTPException(status_code=500, detail="No hay suficientes registros en la base de datos.")
            cache[cache_key] = last_1000_records
            dataOrigin = "Datos obtenidos de la base de datos y almacenados en el caché."

        df_history = pd.DataFrame(last_1000_records)
        df_history.sort_values(by="fecha", inplace=True)

        predictions = []
        for record in last_1000_records:
            record["_id"] = str(record["_id"])
        test = last_1000_records

        predictions_cache_key = "prediccitions"
        if predictions_cache_key in cache_predictions:
            predictions = cache_predictions[predictions_cache_key]
            dataOrigin += 'predictiones '
            response_data = {"predicciones": predictions, "dataOrigin": dataOrigin}
            return JSONResponse(content=json.loads(json.dumps(response_data, default=str)))
        ## Bucle que realiza predicciones para los siguientes 7 días
        for i in range(7):
            # Calcula la fecha del día de predicción (sumando i días a la fecha actual)
            pred_day = datetime.now() + timedelta(days=i)
            # Calcula el día del año a partir de la fecha de predicción
            day_of_year = pred_day.timetuple().tm_yday
            # Calcula las funciones trigonométricas del día del año (para capturar la estacionalidad)
            sin_day = np.sin(2 * np.pi * day_of_year / 365.0)
            cos_day = np.cos(2 * np.pi * day_of_year / 365.0)
            #Diccionario para almacenar los datos retardados (lags) de las variables relevantes
            lagged_data = {}
            # Genera los lags para las columnas de interés (temperatura, humedad, etc.)
            for lag in range(1, 101):
                for col in ["temperatura", "humedad", "presion_atmosferica", "radiacion_solar", "lluvia"]:
                    lagged_data[f"{col}_lag{lag}"] = df_history[col].shift(lag).iloc[-1]

            #Generar variables mobiles
            for col in ["temperatura", "humedad", "presion_atmosferica", "radiacion_solar"]:
                df_history[f"{col}_rolling_30"] = df_history[col].rolling(window=30, min_periods=1).mean()
                df_history[f"{col}_rolling_90"] = df_history[col].rolling(window=90, min_periods=1).mean()
             # Prepara los datos para la predicción de regresión (valores retardados y funciones trigonométricas)
            X_reg_input = pd.DataFrame([lagged_data], columns=[f"{col}_lag{lag}" for lag in range(1, 101) for col in ["temperatura", "humedad", "presion_atmosferica", "radiacion_solar"]])
            X_reg_input["sin_dayofyear"] = sin_day
            X_reg_input["cos_dayofyear"] = cos_day
             # Añade las medias móviles a los datos de entrada
            for col in ["temperatura", "humedad", "presion_atmosferica", "radiacion_solar"]:
                X_reg_input[f"{col}_rolling_30"] = df_history[f"{col}_rolling_30"].iloc[-1]
                X_reg_input[f"{col}_rolling_90"] = df_history[f"{col}_rolling_90"].iloc[-1]
            # Filtra las columnas necesarias para la predicción de regresión
            X_reg_input = X_reg_input[reg_columns]
            # Prepara los datos para la predicción de clasificación (añadiendo lags de lluvia y otras variables)
            X_clf_input = pd.DataFrame([lagged_data], columns=[f"{col}_lag{lag}" for lag in range(1, 101) for col in ["temperatura", "humedad", "presion_atmosferica", "radiacion_solar"]])
            X_clf_input["sin_dayofyear"] = sin_day
            X_clf_input["cos_dayofyear"] = cos_day
             # Añade las medias móviles a los datos de entrada de clasificación
            for col in ["temperatura", "humedad", "presion_atmosferica", "radiacion_solar"]:
                X_clf_input[f"{col}_rolling_30"] = df_history[f"{col}_rolling_30"].iloc[-1]
                X_clf_input[f"{col}_rolling_90"] = df_history[f"{col}_rolling_90"].iloc[-1]
             # Añade los lags de lluvia al conjunto de datos de clasificación
            X_clf_input[[f"lluvia_lag{lag}" for lag in range(1, 101)]] = pd.DataFrame([lagged_data], columns=[f"lluvia_lag{lag}" for lag in range(1, 101)])
            # Filtra las columnas necesarias para la predicción de clasificación
            X_clf_input = X_clf_input[clf_columns]
             # Realiza la predicción de regresión (temperatura, humedad, presión, radiación)
            reg_output = model_reg.predict(X_reg_input)[0]
            # Realiza la predicción de clasificación (probabilidad de lluvia)
            clf_proba = model_clf.predict_proba(X_clf_input)[0][1]
             # Extrae los valores de predicción de la regresión
            temp_d, hum_d, pres_d, rad_d = reg_output
              # Crea el objeto con la predicción del día
            pred = {
                "fecha": pred_day.strftime("%Y-%m-%d"),
                "temperatura_predicha": f"{temp_d:.2f} °C",
                "humedad_predicha": f"{hum_d:.2f} %",
                "presion_predicha": f"{pres_d:.2f} hPa",
                "radiacion_predicha": f"{rad_d:.2f} W/m²",
                "probabilidad_lluvia": f"{clf_proba * 100:.2f} %"
            }
             # Añade la predicción a la lista de predicciones
            predictions.append(pred)
             # Actualiza la base de datos con la nueva predicción (si ya existe, actualiza, si no, inserta)
            collection.update_one(
                {"fecha": pred_day},
                {"$set": pred},
                upsert=True
            )
            # Crea un nuevo registro para añadirlo al DataFrame de histórico
            new_row = {
                "fecha": pred_day,
                "temperatura": temp_d,
                "humedad": hum_d,
                "presion_atmosferica": pres_d,
                "radiacion_solar": rad_d,
                "lluvia": clf_proba
            }
            # Añade el nuevo registro al DataFrame histórico
            df_history = pd.concat([df_history, pd.DataFrame([new_row])], ignore_index=True)
            # Limita el DataFrame a las últimas 100 observaciones
            df_history = df_history.tail(100)
        # Almacena las predicciones en caché para evitar recalcularlas en futuras peticiones
        response_data = {"predicciones": predictions, "dataOrigin": dataOrigin}
        cache_predictions[predictions_cache_key] = predictions
        return JSONResponse(content=json.loads(json.dumps(response_data, default=str)))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
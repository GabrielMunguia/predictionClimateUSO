import os
import pymongo
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import joblib
import numpy as np
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/predict")

model_reg = None
model_clf = None

# Conectar a MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["tesis"]
collection = db["history2"]

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
        if model_reg is None or model_clf is None:
            raise ValueError("Los modelos no están cargados.")

        # 1. Obtener el último registro desde MongoDB
        last_record = collection.find().sort("fecha", -1).limit(1)
        last_record = list(last_record)

        if not last_record:
            raise HTTPException(status_code=500, detail="No hay registros en la base de datos.")

       
        last_record = last_record[0]  # Extraer el documento
        current_lag = {
            "temp_lag1": last_record["temperatura"],
            "hum_lag1": last_record["humedad"],
            "pres_lag1": last_record["presion_atmosferica"],
            "rad_lag1": last_record["radiacion_solar"],
            "lluvia_lag1": last_record["lluvia"]
        }

        predictions = []

        for i in range(7):
            pred_day = datetime.now() + timedelta(days=i)
            day_of_year = pred_day.timetuple().tm_yday

            sin_day = np.sin(2 * np.pi * day_of_year / 365.0)
            cos_day = np.cos(2 * np.pi * day_of_year / 365.0)

            X_reg_input = pd.DataFrame([[
                current_lag["temp_lag1"],
                current_lag["hum_lag1"],
                current_lag["pres_lag1"],
                current_lag["rad_lag1"],
                sin_day,
                cos_day
            ]], columns=["temp_lag1", "hum_lag1", "pres_lag1", "rad_lag1", "sin_dayofyear", "cos_dayofyear"])

            X_clf_input = pd.DataFrame([[
                current_lag["temp_lag1"],
                current_lag["hum_lag1"],
                current_lag["pres_lag1"],
                current_lag["rad_lag1"],
                sin_day,
                cos_day,
                current_lag["lluvia_lag1"]
            ]], columns=["temp_lag1", "hum_lag1", "pres_lag1", "rad_lag1", "sin_dayofyear", "cos_dayofyear", "lluvia_lag1"])

            # 2. Realizar predicciones
            reg_output = model_reg.predict(X_reg_input)[0]  # [temp_d, hum_d, pres_d, rad_d]
            clf_proba = model_clf.predict_proba(X_clf_input)[0][1]  # Probabilidad de lluvia

            temp_d, hum_d, pres_d, rad_d = reg_output

            if (i==0):
                 pred = {
                  "fecha": last_record["fecha"].strftime("%Y-%m-%d"),  # Fecha del último registro
                  "temperatura_predicha": f"{current_lag['temp_lag1']:.2f} °C",
                  "humedad_predicha": f"{current_lag['hum_lag1']:.2f} %",
                  "presion_predicha": f"{current_lag['pres_lag1']:.2f} hPa",
                  "radiacion_predicha": f"{current_lag['rad_lag1']:.2f} W/m²",
                  "probabilidad_lluvia": f"{clf_proba*100:.2f} %"
                }
            else:

               pred = {
                   "fecha": pred_day.strftime("%Y-%m-%d"),
                   "temperatura_predicha": f"{temp_d:.2f} °C",
                   "humedad_predicha": f"{hum_d:.2f} %",
                   "presion_predicha": f"{pres_d:.2f} hPa",
                   "radiacion_predicha": f"{rad_d:.2f} W/m²",
                   "probabilidad_lluvia": f"{clf_proba*100:.2f} %"
               }

            predictions.append(pred)

            # 3. Guardar la predicción en la base de datos (opcional)
            collection.update_one(
                {"fecha": pred_day},
                {"$set": pred},
                upsert=True
            )

            # 4. Actualizar las lags para la siguiente iteración
            current_lag["temp_lag1"] = temp_d
            current_lag["hum_lag1"] = hum_d
            current_lag["pres_lag1"] = pres_d
            current_lag["rad_lag1"] = rad_d
            current_lag["lluvia_lag1"] = (clf_proba)  

        return JSONResponse(content={"predicciones": predictions})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

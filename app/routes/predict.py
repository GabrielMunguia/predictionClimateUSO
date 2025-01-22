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
    """
    Ejemplo de predicción encadenada a 7 días
    con modelo entrenado en enfoque de series de tiempo (lags).
    """
    try:
        if model_reg is None or model_clf is None:
            raise ValueError("Los modelos no están cargados.")

        # -----------------------------
        # Paso 1. Definir el estado inicial (valores de *ayer*)
        # Necesitamos temp_lag1, hum_lag1, etc. como "último registro" real
        # o asumido. Supón que hoy es 2025-01-12, tenemos los datos de
        # 2025-01-11 en la DB. 
        # Aquí, a modo de ejemplo, inicializamos manualmente:
        current_lag = {
            "temp_lag1": 29.0,
            "hum_lag1": 45.0,
            "pres_lag1": 1009.8,
            "rad_lag1": 717.5,
            "lluvia_lag1": 0
        }

        # Para cada predicción, necesitamos sin_dayofyear y cos_dayofyear del DÍA
        # a predecir. (Porque en el entrenamiento, day_of_year correspondía al día actual).
        
        predictions = []

        for i in range(7):
            pred_day = datetime.now() + timedelta(days=i)
            day_of_year = pred_day.timetuple().tm_yday

            sin_day = np.sin(2*np.pi*day_of_year/365.0)
            cos_day = np.cos(2*np.pi*day_of_year/365.0)

            # Construimos el DataFrame con las "lags" + day_of_year
            X_reg_input = pd.DataFrame([[
                current_lag["temp_lag1"],
                current_lag["hum_lag1"],
                current_lag["pres_lag1"],
                current_lag["rad_lag1"],
                sin_day,
                cos_day
            ]],
            columns = [
                "temp_lag1",
                "hum_lag1",
                "pres_lag1",
                "rad_lag1",
                "sin_dayofyear",
                "cos_dayofyear"
            ])

            # Para la clasificación (lluvia), incluimos lluvia_lag1
            X_clf_input = pd.DataFrame([[
                current_lag["temp_lag1"],
                current_lag["hum_lag1"],
                current_lag["pres_lag1"],
                current_lag["rad_lag1"],
                sin_day,
                cos_day,
                current_lag["lluvia_lag1"]
            ]],
            columns = [
                "temp_lag1",
                "hum_lag1",
                "pres_lag1",
                "rad_lag1",
                "sin_dayofyear",
                "cos_dayofyear",
                "lluvia_lag1"
            ])

            # -----------------------------
            # Paso 2. Realizar la predicción
            reg_output = model_reg.predict(X_reg_input)[0]  # array con 4 valores
            clf_proba = model_clf.predict_proba(X_clf_input)[0][1]  # prob lluvia

            # reg_output => [temp_d, hum_d, pres_d, rad_d]
            temp_d, hum_d, pres_d, rad_d = reg_output

            predictions.append({
                "fecha": pred_day.strftime("%Y-%m-%d"),
                "temperatura_predicha": f"{temp_d:.2f} °C",
                "humedad_predicha": f"{hum_d:.2f} %",
                "presion_predicha": f"{pres_d:.2f} hPa",
                "radiacion_predicha": f"{rad_d:.2f} W/m²",
                "probabilidad_lluvia": f"{clf_proba*100:.2f} %"
            })

            # -----------------------------
            # Paso 3. Actualizar las lags para la siguiente iteración
            # El día que acabamos de predecir (d) se convierte en el "lag" para el día (d+1)
            current_lag["temp_lag1"] = temp_d
            current_lag["hum_lag1"]  = hum_d
            current_lag["pres_lag1"] = pres_d
            current_lag["rad_lag1"]  = rad_d
            # Binarizamos lluvia pronosticada, por ejemplo, si clf_proba>0.5 => 1
            current_lag["lluvia_lag1"] = int(clf_proba > 0.5)

        return JSONResponse(content={"predicciones": predictions})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
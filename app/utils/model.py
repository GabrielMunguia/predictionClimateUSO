import pymongo
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_squared_error, classification_report
import joblib

def traningModel():
    print("Entrenando modelo.....")
    # 1. Conexión a MongoDB
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["tesis"]
    collection = db["history2"]
    
    # 2. Cargar datos en DataFrame
    data = pd.DataFrame(list(collection.find()))
    if data.empty:
        print("Error: No se encontraron datos en la colección 'history2'.")
        return

    # 3. Convertir 'fecha' a tipo datetime y ordenar por fecha
    data["fecha"] = pd.to_datetime(data["fecha"], errors='coerce')
    data.sort_values(by="fecha", inplace=True)

    # 4. Mantener solo las columnas relevantes (asegúrate de que existan)
    required_columns = [
        "fecha",
        "temperatura",
        "humedad",
        "presion_atmosferica",
        "radiacion_solar",
        "lluvia"
    ]
    data = data[[c for c in required_columns if c in data.columns]]

    # Elimina filas con nulos en las columnas críticas
    data.dropna(subset=["temperatura", "humedad", "presion_atmosferica", "radiacion_solar", "lluvia"], inplace=True)

    # Binarizar lluvia si viene en mm
    data["lluvia"] = (data["lluvia"] > 0).astype(int)

    # 5. Crear las columnas de rezago (lag de 1 día)
    #    Para cada variable que quieras predecir, haz un shift(1)
    data["temp_lag1"] = data["temperatura"].shift(1)
    data["hum_lag1"]  = data["humedad"].shift(1)
    data["pres_lag1"] = data["presion_atmosferica"].shift(1)
    data["rad_lag1"]  = data["radiacion_solar"].shift(1)
    data["lluvia_lag1"] = data["lluvia"].shift(1)  # Para el modelo de lluvia

    # 6. Crear las variables “target” a predecir para el día d
    #    (opcionalmente, podrías predecir el día d+1 haciendo shift(-1), 
    #     pero en este ejemplo predecimos el día d a partir del d-1).
    #    *Si quieres EXACTAMENTE "hoy" <- "ayer", dejas así.
    #    *Si prefieres "mañana" <- "hoy", usas shift(-1) en los targets.
    #    Aquí haré: Y[d] <- X[d-1].
    #    Por lo tanto, X estará en filas “d” pero con info de “d-1”.
    #    Y estará en filas “d” con su propia info (temperatura del día d).
    #    => Eliminamos la primera fila (porque lag1 es NaN).
    
    # 7. Variables cíclicas del DIA (para el día d real)
    data["day_of_year"] = data["fecha"].dt.dayofyear
    data["sin_dayofyear"] = np.sin(2 * np.pi * data["day_of_year"] / 365)
    data["cos_dayofyear"] = np.cos(2 * np.pi * data["day_of_year"] / 365)

    # Ahora, eliminamos las primeras filas que tengan NaN en lags
    data.dropna(subset=["temp_lag1", "hum_lag1", "pres_lag1", "rad_lag1"], inplace=True)

    # 8. Definir features (X) y targets (Y)
    #    - X: valores del día (d-1) + sin/cos del día actual (d)
    #    - Y: valores del día actual (d)
    
    # Features para REGRESIÓN
    # (para predecir temp, humedad, pres, radiación del día d)
    regression_features = [
        "temp_lag1",
        "hum_lag1",
        "pres_lag1",
        "rad_lag1",
        "sin_dayofyear",
        "cos_dayofyear"
    ]
    # Target (OUTPUT) en la parte de regresión
    regression_targets = [
        "temperatura",
        "humedad",
        "presion_atmosferica",
        "radiacion_solar"
    ]

    X_reg = data[regression_features].copy()
    Y_reg = data[regression_targets].copy()

    # Features para CLASIFICACIÓN (lluvia)
    classification_features = [
        "temp_lag1",
        "hum_lag1",
        "pres_lag1",
        "rad_lag1",
        "sin_dayofyear",
        "cos_dayofyear",
        "lluvia_lag1"  # Quizá quieras también la lluvia del día anterior
    ]
    X_clf = data[classification_features].copy()
    Y_clf = data["lluvia"].copy()

    # 9. Partir en train/test (ejemplo: 80/20)
    train_size = int(len(data) * 0.8)

    X_reg_train, X_reg_test = X_reg.iloc[:train_size], X_reg.iloc[train_size:]
    Y_reg_train, Y_reg_test = Y_reg.iloc[:train_size], Y_reg.iloc[train_size:]

    X_clf_train, X_clf_test = X_clf.iloc[:train_size], X_clf.iloc[train_size:]
    Y_clf_train, Y_clf_test = Y_clf.iloc[:train_size], Y_clf.iloc[train_size:]

    # 10. Entrenar modelo de regresión (multi-output)
    regressor = MultiOutputRegressor(
        RandomForestRegressor(
            n_estimators=100,
            random_state=42
        )
    )
    regressor.fit(X_reg_train, Y_reg_train)

    # Métrica
    reg_preds = regressor.predict(X_reg_test)
    mse_vals = mean_squared_error(Y_reg_test, reg_preds, multioutput='raw_values')
    print("MSE (Regresión) en test:")
    for i, col in enumerate(regression_targets):
        print(f"  {col}: {mse_vals[i]:.2f}")

    # 11. Entrenar modelo de clasificación para lluvia
    classifier = RandomForestClassifier(
        n_estimators=100,
        random_state=42
    )
    classifier.fit(X_clf_train, Y_clf_train)

    clf_preds = classifier.predict(X_clf_test)
    print("\nReporte clasificación (test):")
    print(classification_report(Y_clf_test, clf_preds))

    # 12. Guardar modelos
    joblib.dump(regressor, "modelo_clima_regresion.pkl")
    joblib.dump(classifier, "modelo_clima_clasificacion.pkl")
    print("\n¡Modelos de serie de tiempo entrenados y guardados exitosamente!")

    return regressor, classifier
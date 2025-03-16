import pymongo
import pandas as pd
import numpy as np
import joblib
from tqdm import tqdm

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_squared_error, classification_report

# Parámetro para definir cuántos días de historial usar para generar Lags
MAX_LAGS  = 100




# Conexión a MongoDB
#Conecta a la base de datos MongoDB y carga los datos desde la colección history2 en un DataFrame de pandas. Si no se encuentran datos o hay un error, lo reporta.
def load_data_from_mongo():
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["tesis"]
        collection = db["history2"]
        data = pd.DataFrame(list(collection.find()))

        if data.empty:
            raise ValueError("No se encontraron datos en la colección 'history2'.")
        return data
    except Exception as e:
        print(f"Error al cargar datos de MongoDB: {e}")
        return None

# Preprocesamiento de datos
# preprocess_data: Realiza una serie de pasos para preparar los datos:
# Convierte la columna fecha a formato datetime y ordena los datos por fecha.
# Verifica que las columnas necesarias estén presentes y limpia los datos.
# Convierte la variable lluvia en una variable binaria.
# Genera las características lag para cada variable relevante.
# Agrega variables cíclicas del día del año (sin y cos).
# Calcula promedios móviles para variables clave.
# Elimina cualquier fila con valores faltantes generados por los lags o promedios móviles.
def preprocess_data(data):
    print("Preprocesando datos...")

    # Convertir 'fecha' a datetime y ordenar
    data["fecha"] = pd.to_datetime(data["fecha"], errors='coerce')
    data.sort_values(by="fecha", inplace=True)

    # Selección de columnas relevantes
    required_columns = {"fecha", "temperatura", "humedad", "presion_atmosferica", "radiacion_solar", "lluvia"}
    available_columns = set(data.columns)
    missing_columns = required_columns - available_columns

    if missing_columns:
        raise ValueError(f"Faltan columnas en los datos: {missing_columns}")

    data = data[list(required_columns)].copy()
    data.dropna(subset=required_columns - {"fecha"}, inplace=True)

    # Convertir lluvia a variable binaria
    data["lluvia"] = (data["lluvia"] > 0).astype(int)

    # Generar los lags para todos los datos disponibles
    max_lag = MAX_LAGS 
    lagged_data = {}

    for lag in tqdm(range(1, max_lag + 1), desc="Generando lags"):
        for col in ["temperatura", "humedad", "presion_atmosferica", "radiacion_solar", "lluvia"]:
            lagged_data[f"{col}_lag{lag}"] = data[col].shift(lag)

    # Unir todas las columnas de lags con el dataframe original
    lagged_df = pd.DataFrame(lagged_data, index=data.index)
    data = pd.concat([data, lagged_df], axis=1)

    # Variables cíclicas del día
    data["day_of_year"] = data["fecha"].dt.dayofyear
    data["sin_dayofyear"] = np.sin(2 * np.pi * data["day_of_year"] / 365)
    data["cos_dayofyear"] = np.cos(2 * np.pi * data["day_of_year"] / 365)

    # Calcular promedios móviles
    for col in ["temperatura", "humedad", "presion_atmosferica", "radiacion_solar"]:
        data[f"{col}_rolling_30"] = data[col].rolling(window=30, min_periods=1).mean()
        data[f"{col}_rolling_90"] = data[col].rolling(window=90, min_periods=1).mean()

    # Eliminar filas con NaN generados por los lags y promedios móviles
    data.dropna(inplace=True)

    return data

# División en train/test

# split_data: Divide los datos en conjuntos de entrenamiento y prueba para dos tareas:
# Regresión: Predicción de variables continuas (temperatura, humedad, etc.).
# Clasificación: Predicción de la variable lluvia como un valor binario.
# Separamos las características y objetivos, y asignamos el 80% de los datos al entrenamiento y el 20% a la prueba.
def split_data(data):
    train_size = int(len(data) * 0.8)

    feature_columns = [f"{col}_lag{lag}" for lag in range(1, MAX_LAGS  + 1) for col in ["temperatura", "humedad", "presion_atmosferica", "radiacion_solar"]]
    feature_columns += ["sin_dayofyear", "cos_dayofyear"]
    feature_columns += [f"{col}_rolling_30" for col in ["temperatura", "humedad", "presion_atmosferica", "radiacion_solar"]]
    feature_columns += [f"{col}_rolling_90" for col in ["temperatura", "humedad", "presion_atmosferica", "radiacion_solar"]]

    target_columns = ["temperatura", "humedad", "presion_atmosferica", "radiacion_solar"]

    X_reg_train, X_reg_test = data[feature_columns][:train_size], data[feature_columns][train_size:]
    Y_reg_train, Y_reg_test = data[target_columns][:train_size], data[target_columns][train_size:]

    feature_columns_clf = feature_columns + [f"lluvia_lag{lag}" for lag in range(1, MAX_LAGS  + 1)]
    X_clf_train, X_clf_test = data[feature_columns_clf][:train_size], data[feature_columns_clf][train_size:]
    Y_clf_train, Y_clf_test = data["lluvia"][:train_size], data["lluvia"][train_size:]

    return X_reg_train, X_reg_test, Y_reg_train, Y_reg_test, X_clf_train, X_clf_test, Y_clf_train, Y_clf_test

# Entrenamiento de modelos
# train_models: Entrena dos modelos utilizando Random Forest:
# Regresor: Para predecir múltiples variables continuas.
# Clasificador: Para predecir la variable lluvia binaria.
# Utiliza MultiOutputRegressor para entrenar múltiples salidas en el regresor.
def train_models(X_reg_train, Y_reg_train, X_clf_train, Y_clf_train):
    print("Entrenando modelos...")

    regressor = MultiOutputRegressor(RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1))
    regressor.fit(X_reg_train, Y_reg_train)

    classifier = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    classifier.fit(X_clf_train, Y_clf_train)

    return regressor, classifier

# Evaluación de modelos
# evaluate_models: Evalúa los modelos entrenados:
# Regresor: Calcula el error cuadrático medio (MSE) para cada variable predicha.
# Clasificador: Imprime el reporte de clasificación para la predicción de lluvia, mostrando precisión, recall, f1-score, etc.
def evaluate_models(regressor, X_reg_test, Y_reg_test, classifier, X_clf_test, Y_clf_test):
    print("\nEvaluando modelos...")

    reg_preds = regressor.predict(X_reg_test)
    mse_vals = mean_squared_error(Y_reg_test, reg_preds, multioutput='raw_values')

    print("\nMSE (Regresión) en test:")
    for col, mse in zip(Y_reg_test.columns, mse_vals):
        print(f"  {col}: {mse:.2f}")

    clf_preds = classifier.predict(X_clf_test)
    print("\nReporte de clasificación (lluvia):")
    print(classification_report(Y_clf_test, clf_preds))

# Guardado de modelos
# save_models: Guarda los modelos entrenados en archivos .pkl utilizando joblib.
def save_models(regressor, classifier):
    joblib.dump(regressor, "modelo_clima_regresion.pkl")
    joblib.dump(classifier, "modelo_clima_clasificacion.pkl")
    print("\n¡Modelos guardados exitosamente!")

# Función principal
def traningModel():
    print("Iniciando entrenamiento del modelo...")

    data = load_data_from_mongo()
    if data is None:
        return

    try:
        data = preprocess_data(data)
        X_reg_train, X_reg_test, Y_reg_train, Y_reg_test, X_clf_train, X_clf_test, Y_clf_train, Y_clf_test = split_data(data)

        regressor, classifier = train_models(X_reg_train, Y_reg_train, X_clf_train, Y_clf_train)
        evaluate_models(regressor, X_reg_test, Y_reg_test, classifier, X_clf_test, Y_clf_test)
        save_models(regressor, classifier)

        print("\n¡Entrenamiento finalizado con éxito!")
        return regressor, classifier
    except Exception as e:
        print(f"Error en el proceso de entrenamiento: {e}")

# Llamar a la función principal
#traningModel()
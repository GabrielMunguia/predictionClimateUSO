import joblib
import pandas as pd
from sklearn.metrics import mean_squared_error, classification_report

# Carga los modelos .pkl
regressor = joblib.load("modelo_clima_regresion.pkl")  # Reemplaza con la ruta correcta
classifier = joblib.load("modelo_clima_clasificacion.pkl") # Reemplaza con la ruta correcta

# Carga los datos de prueba (reemplaza con tus datos reales)
# Aquí se asume que tienes X_reg_test, Y_reg_test, X_clf_test, Y_clf_test ya definidos
# Puedes cargar tus datos desde un archivo CSV o DataFrame
# Ejemplo:
# X_reg_test = pd.read_csv("X_reg_test.csv")
# Y_reg_test = pd.read_csv("Y_reg_test.csv")
# X_clf_test = pd.read_csv("X_clf_test.csv")
# Y_clf_test = pd.read_csv("Y_clf_test.csv")

# Realiza predicciones con el modelo de regresión
reg_preds = regressor.predict(X_reg_test)

# Evalúa el modelo de regresión
mse_vals = mean_squared_error(Y_reg_test, reg_preds, multioutput='raw_values')
print("MSE (Regresión):")
for col, mse in zip(Y_reg_test.columns, mse_vals):
    print(f"  {col}: {mse:.2f}")

# Realiza predicciones con el modelo de clasificación
clf_preds = classifier.predict(X_clf_test)

# Evalúa el modelo de clasificación
print("\nReporte de Clasificación (Lluvia):")
print(classification_report(Y_clf_test, clf_preds))
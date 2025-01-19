# Climapredict API

Climapredict es una API para la predicción climática que te permite obtener pronósticos del tiempo a través de una sencilla interfaz. Esta API utiliza modelos de predicción climática para ofrecer datos sobre el clima en diferentes ubicaciones.

## Requisitos

Antes de ejecutar la API, asegúrate de tener instalados los siguientes programas:

- [Python 3.8+](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/) para la gestión de dependencias.

## Instalación

Sigue los siguientes pasos para instalar y ejecutar la API de Climapredict en tu máquina local:

### 1. Crear y activar un entorno virtual

Es recomendable crear un entorno virtual para evitar conflictos con otras dependencias de Python. Ejecuta los siguientes comandos en tu terminal para crear y activar el entorno virtual:

```bash
# En sistemas Windows
python -m venv climapredict
source climapredict/Scripts/activate

# En sistemas Mac/Linux
python3 -m venv climapredict
source climapredict/bin/activate
```

### 2. Instalar las dependencias

Instala las dependencias necesarias utilizando el archivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Ejecutar la API

Para iniciar el servidor de desarrollo y probar la API localmente, utiliza `uvicorn`, que ejecutará tu aplicación en modo de recarga automática:

```bash
uvicorn main:app --reload
```
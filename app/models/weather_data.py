from datetime import datetime

class WeatherData:
    def __init__(self, data):
        self._id = data.get('_id')
        self.fecha = data.get('fecha', datetime.utcnow())
        self.temperatura_interior = data.get('temperatura_interior')
        self.temperatura = data.get('temperatura')
        self.sensacion_termica = data.get('sensacion_termica')
        self.punto_rocio_interior = data.get('punto_rocío_interior')
        self.punto_rocio = data.get('punto_rocío')
        self.indice_calor_interior = data.get('indice_calor_interior')
        self.indice_calor = data.get('indice_calor')
        self.humedad_interior = data.get('humedad_interior')
        self.humedad = data.get('humedad')
        self.rafaga_maxima_viento = data.get('rafaga_maxima_viento')
        self.velocidad_media_viento = data.get('velocidad_media_viento')
        self.direccion_media_viento = data.get('direccion_media_viento')
        self.presion_atmosferica = data.get('presion_atmosferica')
        self.lluvia = data.get('lluvia')
        self.evapotranspiracion = data.get('evapotranspiracion')
        self.intensidad_lluvia = data.get('intensidad_lluvia')
        self.radiacion_solar = data.get('radiacion_solar')
        self.indice_uv = data.get('indice_uv')

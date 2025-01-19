import os
import pymongo

def getConexionMongo():
    host = os.getenv('MONGO_HOST')
    puerto = int(os.getenv('MONGO_PORT'))
    base_de_datos = os.getenv('MONGO_DB')
    
    cliente = pymongo.MongoClient(host, puerto)
    db = cliente[base_de_datos]
    return db
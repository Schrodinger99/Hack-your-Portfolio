import os
import re
import datetime
from pymongo import MongoClient, errors
from Recommend import Recommend

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"
MIN_EDAD = 18
MAX_EDAD = 100

MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://ivancz:nlZhpOlsRRlZq3pV@cluster0.nq3x0sh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
client = MongoClient(MONGO_URI)
db = client['Platform']
users_collection = db['users']
communities_collection = db['communities']
messages_collection = db['messages']
topics_collection = db['topics']

def inicializar_topicos():
    topicos = [
        {"id": 1, "nombre": "Tecnología"},
        {"id": 2, "nombre": "Ciencia"},
        {"id": 3, "nombre": "Deportes"},
        {"id": 4, "nombre": "Arte"},
        {"id": 5, "nombre": "Música"},
        {"id": 6, "nombre": "Viajes"},
        {"id": 7, "nombre": "Comida"},
        {"id": 8, "nombre": "Finanzas"},
        {"id": 9, "nombre": "Educación"},
        {"id": 10, "nombre": "Cine"},
        {"id": 11, "nombre": "Literatura"},
        {"id": 12, "nombre": "Moda"},
        {"id": 13, "nombre": "Juegos"},
        {"id": 14, "nombre": "Salud"},
        {"id": 15, "nombre": "Tecnología Espacial"}
    ]
    if topics_collection.count_documents({}) == 0:
        topics_collection.insert_many(topicos)

inicializar_topicos()

def validar_usuario(data):
    if not data.get('username'):
        return "El nombre de usuario es obligatorio."
    if not data.get('correo') or not re.match(EMAIL_REGEX, data['correo']):
        return "El correo electrónico no es válido."
    if not data.get('nombre'):
        return "El nombre es obligatorio."
    if not data.get('edad') or not (MIN_EDAD <= int(data['edad']) <= MAX_EDAD):
        return "La edad debe estar entre 18 y 100 años."
    if not data.get('topicos_interes'):
        return "Debe seleccionar al menos un tópico de interés."
    return None

def convertir_topicos_a_tupla(topicos_seleccionados):
    topicos = [t["id"] for t in topics_collection.find({})]
    return tuple(1 if int(topico) in topicos_seleccionados else 0 for topico in topicos)

def registrar_usuario(data):
    error = validar_usuario(data)
    if error:
        return error

    if users_collection.find_one({"username": data['username']}):
        return "El nombre de usuario ya existe."

    topicos_interes = convertir_topicos_a_tupla(list(map(int, data.getlist('topicos_interes'))))

    user = {
        "username": data['username'],
        "correo": data['correo'],
        "nombre": data['nombre'],
        "edad": data['edad'],
        "topicos_interes": topicos_interes,
        "password": data['password'],
        "created_at": datetime.datetime.now()
    }
    users_collection.insert_one(user)
    return "Usuario registrado con éxito."

def enviar_mensaje(data, sender):
    receiver = data.get('receiver')
    content = data.get('content')
    community = data.get('community')

    if not users_collection.find_one({"username": sender}):
        return {"error": "El remitente no existe."}

    if community:
        if not communities_collection.find_one({"name": community}):
            return {"error": "La comunidad no existe."}
    else:
        if not users_collection.find_one({"username": receiver}):
            return {"error": "El destinatario no existe."}

    message = {
        "sender": sender,
        "receiver": receiver,
        "community": community,
        "content": content,
        "timestamp": datetime.datetime.now()
    }
    messages_collection.insert_one(message)
    return "Mensaje enviado con éxito."

def obtener_chats_directos(username):
    mensajes = messages_collection.find({
        "$or": [
            {"sender": username},
            {"receiver": username}
        ],
        "community": None
    })

    chats = set()
    for mensaje in mensajes:
        chats.add(mensaje['sender'])
        chats.add(mensaje['receiver'])

    chats.discard(username)
    return list(chats)

def buscar_usuarios(query):
    if not query:
        return {"error": "Debe proporcionar un término de búsqueda."}

    usuarios = list(users_collection.find({"username": {"$regex": query, "$options": "i"}}, {"_id": 0, "username": 1, "nombre": 1}))
    return usuarios

def anadir_amigo(username, amigo_username):
    if not username or not amigo_username:
        return {"error": "Debe proporcionar el nombre de usuario del amigo."}

    user = users_collection.find_one({"username": username})
    amigo = users_collection.find_one({"username": amigo_username})
    if not user or not amigo:
        return {"error": "El usuario o el amigo no existen."}

    if "amigos" not in user:
        user["amigos"] = []

    if amigo_username in user["amigos"]:
        return {"error": f"El usuario {username} ya tiene como amigo a {amigo_username}."}

    user["amigos"].append(amigo_username)
    users_collection.update_one({"username": username}, {"$set": {"amigos": user["amigos"]}})
    return "Amigo añadido con éxito."

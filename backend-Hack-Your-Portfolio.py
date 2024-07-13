from flask import Flask, request, jsonify
import os
import json
import re
import datetime
from bson import ObjectId
from pymongo import MongoClient, errors

# Definimos constantes necesarias para la validación
EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"
MIN_EDAD = 18
MAX_EDAD = 100
USUARIOS_PATH = "usuarios.json"
COMUNIDADES_PATH = "comunidades.json"
TOPICOS_PATH = "topicos.json"

# Configuración de la conexión a la base de datos MongoDB
client = MongoClient('localhost', 27017)
db = client['sistema_mensajeria']
users_collection = db['usuarios']
communities_collection = db['comunidades']
messages_collection = db['mensajes']

app = Flask(__name__)

# Función para cargar un archivo JSON
def cargar_json(path):
    try:
        if os.path.exists(path):
            with open(path, 'r') as file:
                return json.load(file)
        return []
    except Exception as e:
        print(f"Error al cargar datos de {path}: {e}")
        return []

# Función para guardar en un archivo JSON
def guardar_json(data, path):
    try:
        with open(path, 'w') as file:
            json.dump(data, file, indent=4, default=str)
    except Exception as e:
        print(f"Error al guardar datos en {path}: {e}")

# Cargar tópicos desde el archivo JSON
topicos = cargar_json(TOPICOS_PATH)

# Definimos las rutas de la API

@app.route('/usuarios', methods=['POST'])
def registrar_usuario():
    """
    Registra un nuevo usuario en el sistema.
    """
    data = request.json
    username = data.get('username')
    correo = data.get('correo')
    nombre = data.get('nombre')
    edad = data.get('edad')
    topicos_interes = data.get('topicos_interes')

    if users_collection.find_one({"username": username}):
        return jsonify({"error": "El nombre de usuario ya existe."}), 400

    user = {
        "username": username,
        "correo": correo,
        "nombre": nombre,
        "edad": edad,
        "topicos_interes": topicos_interes,
        "created_at": datetime.datetime.now()
    }
    users_collection.insert_one(user)
    guardar_usuario_json(user)
    return jsonify(user), 201

@app.route('/login', methods=['POST'])
def login():
    """
    Inicia sesión de un usuario existente.
    """
    data = request.json
    username = data.get('username')

    user = users_collection.find_one({"username": username})
    if user:
        return jsonify(user), 200
    else:
        return jsonify({"error": "Usuario no encontrado. Procediendo al registro."}), 404

@app.route('/mensajes', methods=['POST'])
def enviar_mensaje():
    """
    Envía un mensaje a un usuario o comunidad.
    """
    data = request.json
    sender = data.get('sender')
    receiver = data.get('receiver')
    content = data.get('content')
    community = data.get('community')

    sender_user = users_collection.find_one({"username": sender})
    if not sender_user:
        return jsonify({"error": "El remitente no existe."}), 404

    if community:
        community_doc = communities_collection.find_one({"name": community})
        if not community_doc:
            return jsonify({"error": "La comunidad no existe."}), 404
    else:
        receiver_user = users_collection.find_one({"username": receiver})
        if not receiver_user:
            return jsonify({"error": "El destinatario no existe."}), 404

    message = {
        "sender": sender,
        "receiver": receiver,
        "community": community,
        "content": content,
        "timestamp": datetime.datetime.now()
    }
    messages_collection.insert_one(message)
    return jsonify(message), 201

@app.route('/topicos', methods=['GET'])
def obtener_topicos():
    """
    Obtiene la lista de tópicos.
    """
    return jsonify(topicos), 200

@app.route('/comunidades', methods=['POST'])
def crear_comunidad():
    """
    Crea una nueva comunidad.
    """
    data = request.json
    name = data.get('name')
    description = data.get('description')
    topicos_ids = data.get('topicos_ids')

    if communities_collection.find_one({"name": name}):
        return jsonify({"error": "El nombre de la comunidad ya existe."}), 400

    topicos_binarios = [1 if topico['id'] in topicos_ids else 0 for topico in topicos]

    community = {
        "name": name,
        "description": description,
        "topicos": topicos_binarios,
        "created_at": datetime.datetime.now()
    }
    communities_collection.insert_one(community)
    guardar_comunidad_json(community)
    return jsonify(community), 201

@app.route('/comunidades/unirse', methods=['POST'])
def unirse_a_comunidad():
    """
    Permite a un usuario unirse a una comunidad existente.
    """
    data = request.json
    username = data.get('username')
    community_name = data.get('community_name')

    user = users_collection.find_one({"username": username})
    community = communities_collection.find_one({"name": community_name})
    if not user or not community:
        return jsonify({"error": "El usuario o la comunidad no existen."}), 404

    if "communities" not in user:
        user["communities"] = []

    if community_name in user["communities"]:
        return jsonify({"error": f"El usuario {username} ya es miembro de la comunidad {community_name}."}), 400

    user["communities"].append(community_name)
    users_collection.update_one({"username": username}, {"$set": {"communities": user["communities"]}})
    return jsonify({"message": f"El usuario {username} se ha unido a la comunidad {community_name}."}), 200

@app.route('/comunidades', methods=['GET'])
def mostrar_comunidades():
    """
    Muestra todas las comunidades existentes.
    """
    comunidades = list(communities_collection.find())
    return jsonify(comunidades), 200

if __name__ == '__main__':
    app.run(debug=True)

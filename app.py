from flask import Flask, request, jsonify, session
import os
import re
import datetime
from pymongo import MongoClient
from flask_cors import CORS

# Definimos constantes necesarias para la validación
EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"
MIN_EDAD = 18
MAX_EDAD = 100

# Configuración de la conexión a la base de datos MongoDB
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://alantomasrv:wtsNrKcCKheun2jo@portafolio.1nxjx3j.mongodb.net/?retryWrites=true&w=majority&appName=Portafolio')
client = MongoClient(MONGO_URI)
db = client['sistema_mensajeria']
users_collection = db['usuarios']
communities_collection = db['comunidades']
messages_collection = db['mensajes']
topics_collection = db['topicos']

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'secret_key')
CORS(app)

# Función para inicializar tópicos en la base de datos si no existen
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

# Inicializar tópicos
inicializar_topicos()

# Función para validar un usuario
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

# Rutas de la aplicación

@app.route('/')
def inicio():
    return jsonify({"message": "Bienvenido a la API de mensajería"})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = users_collection.find_one({"username": username})
    if user and user['password'] == password:
        session['username'] = username  # Iniciar sesión
        return jsonify({"message": "Login exitoso"})
    else:
        return jsonify({"error": "Credenciales inválidas"}), 401

@app.route('/registro', methods=['POST'])
def registro():
    data = request.json
    error = validar_usuario(data)
    if error:
        return jsonify({"error": error}), 400

    if users_collection.find_one({"username": data['username']}):
        return jsonify({"error": "El nombre de usuario ya existe"}), 400

    topicos_interes = convertir_topicos_a_tupla(list(map(int, data.get('topicos_interes'))))

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
    return jsonify({"message": "Registro exitoso"})

@app.route('/mensajeria')
def mensajeria():
    if 'username' not in session:
        return jsonify({"error": "Debe iniciar sesión"}), 401
    username = session['username']
    chats_directos = obtener_chats_directos(username)
    return jsonify({"chats_directos": chats_directos})

@app.route('/logout')
def logout():
    session.pop('username', None)
    return jsonify({"message": "Sesión cerrada"})

@app.route('/mensajes', methods=['POST'])
def enviar_mensaje():
    """
    Envía un mensaje a un usuario o comunidad.
    """
    data = request.json
    sender = session.get('username')
    receiver = data.get('receiver')
    content = data.get('content')
    community = data.get('community')

    if not users_collection.find_one({"username": sender}):
        return jsonify({"error": "El remitente no existe"}), 404

    if community:
        if not communities_collection.find_one({"name": community}):
            return jsonify({"error": "La comunidad no existe"}), 404
    else:
        if not users_collection.find_one({"username": receiver}):
            return jsonify({"error": "El destinatario no existe"}), 404

    message = {
        "sender": sender,
        "receiver": receiver,
        "community": community,
        "content": content,
        "timestamp": datetime.datetime.now()
    }
    messages_collection.insert_one(message)
    return jsonify({"message": "Mensaje enviado"})

@app.route('/mensajes/directo', methods=['GET'])
def listar_mensajes_directo():
    if 'username' not in session:
        return jsonify({"error": "Debe iniciar sesión"}), 401
    username = session['username']
    chats_directos = obtener_chats_directos(username)
    return jsonify({"chats_directos": chats_directos})

@app.route('/mensajes/comunidad', methods=['GET'])
def listar_mensajes_comunidad():
    if 'username' not in session:
        return jsonify({"error": "Debe iniciar sesión"}), 401
    username = session['username']
    comunidades = obtener_comunidades_usuario(username)
    return jsonify({"comunidades": comunidades})

def obtener_comunidades_usuario(username):
    user = users_collection.find_one({"username": username})
    if user and 'communities' in user:
        return user['communities']
    return []

@app.route('/mensajes/directo/<usuario>', methods=['GET'])
def obtener_chat_con_usuario(usuario):
    """
    Obtiene el historial de mensajes con un usuario específico.
    """
    username = session.get('username')
    if not username:
        return jsonify({"error": "Debe iniciar sesión"}), 401

    mensajes = list(messages_collection.find({
        "$or": [
            {"sender": username, "receiver": usuario},
            {"sender": usuario, "receiver": username}
        ],
        "community": None
    }).sort("timestamp", 1))

    return jsonify({"mensajes": mensajes})

@app.route('/mensajes/comunidad/<community>', methods=['GET'])
def obtener_mensajes_comunidad(community):
    """
    Obtiene el historial de mensajes de una comunidad.
    """
    mensajes = list(messages_collection.find({
        "community": community
    }).sort("timestamp", 1))

    return jsonify({"mensajes": mensajes})

@app.route('/topicos', methods=['GET'])
def obtener_topicos():
    """
    Obtiene la lista de tópicos.
    """
    topicos = list(topics_collection.find({}, {"_id": 0, "id": 1, "nombre": 1}))
    return jsonify([{"id": t["id"], "nombre": t["nombre"]} for t in topicos]), 200

@app.route('/comunidades', methods=['GET'])
def mostrar_comunidades():
    """
    Muestra todas las comunidades existentes.
    """
    comunidades = list(communities_collection.find())
    return jsonify([{"name": c["name"], "description": c["description"]} for c in comunidades]), 200

@app.route('/comunidades/<comunidad>', methods=['GET'])
def mostrar_comunidad(comunidad):
    """
    Muestra los detalles de una comunidad específica.
    """
    comunidad = communities_collection.find_one({"name": comunidad})
    if not comunidad:
        return jsonify({"error": "La comunidad no existe"}), 404
    mensajes = list(messages_collection.find({"community": comunidad["name"]}).sort("timestamp", 1))
    return jsonify({"comunidad": comunidad, "mensajes": mensajes})

@app.route('/comunidades/unirse', methods=['POST'])
def unirse_a_comunidad():
    """
    Permite a un usuario unirse a una comunidad existente.
    """
    data = request.json
    username = session.get('username')
    community_name = data.get('community_name')

    user = users_collection.find_one({"username": username})
    community = communities_collection.find_one({"name": community_name})
    if not user or not community:
        return jsonify({"error": "El usuario o la comunidad no existen"}), 404

    if "communities" not in user:
        user["communities"] = []

    if community_name in user["communities"]:
        return jsonify({"error": f"El usuario {username} ya es miembro de la comunidad {community_name}"}), 400

    user["communities"].append(community_name)
    users_collection.update_one({"username": username}, {"$set": {"communities": user["communities"]}})
    return jsonify({"message": f"El usuario {username} se ha unido a la comunidad {community_name}"}), 200

@app.route('/chats/directos', methods=['GET'])
def obtener_chats_directos():
    """
    Obtiene la lista de chats directos del usuario.
    """
    if 'username' not in session:
        return jsonify({"error": "Debe iniciar sesión"}), 401
    username = session['username']

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
    return jsonify(list(chats)), 200

@app.route('/usuarios/buscar', methods=['GET'])
def buscar_usuarios():
    """
    Busca usuarios por nombre de usuario.
    """
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Debe proporcionar un término de búsqueda"}), 400

    usuarios = list(users_collection.find({"username": {"$regex": query, "$options": "i"}}, {"_id": 0, "username": 1, "nombre": 1}))
    return jsonify(usuarios), 200

@app.route('/amigos/anadir', methods=['POST'])
def anadir_amigo():
    """
    Añade un amigo a la lista de amigos del usuario.
    """
    data = request.json
    username = session.get('username')
    amigo_username = data.get('amigo_username')

    if not username or not amigo_username:
        return jsonify({"error": "Debe proporcionar el nombre de usuario del amigo"}), 400

    user = users_collection.find_one({"username": username})
    amigo = users_collection.find_one({"username": amigo_username})
    if not user or not amigo:
        return jsonify({"error": "El usuario o el amigo no existen"}), 404

    if "amigos" not in user:
        user["amigos"] = []

    if amigo_username in user["amigos"]:
        return jsonify({"error": f"El usuario {username} ya tiene como amigo a {amigo_username}"}), 400

    user["amigos"].append(amigo_username)
    users_collection.update_one({"username": username}, {"$set": {"amigos": user["amigos"]}})
    return jsonify({"message": f"El usuario {username} ha agregado a {amigo_username} como amigo"}), 200

if __name__ == '__main__':
    try:
        app.run(debug=True)
    except Exception as e:
        print(f"An error occurred: {e}")
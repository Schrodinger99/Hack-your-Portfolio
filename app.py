from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import os
import re
import datetime
from pymongo import MongoClient, errors

# Definimos constantes necesarias para la validación
EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"
MIN_EDAD = 18
MAX_EDAD = 100

# Configuración de la conexión a la base de datos MongoDB
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['sistema_mensajeria']
users_collection = db['usuarios']
communities_collection = db['comunidades']
messages_collection = db['mensajes']
topics_collection = db['topicos']

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'secret_key')

# Función para inicializar tópicos en la base de datos si no existen
def inicializar_topicos():
    topicos = [
        {"nombre": "Tecnología"},
        {"nombre": "Ciencia"},
        {"nombre": "Deportes"},
        {"nombre": "Arte"},
        {"nombre": "Música"},
        {"nombre": "Viajes"},
        {"nombre": "Comida"},
        {"nombre": "Finanzas"},
        {"nombre": "Educación"},
        {"nombre": "Cine"},
        {"nombre": "Literatura"},
        {"nombre": "Moda"},
        {"nombre": "Juegos"},
        {"nombre": "Salud"},
        {"nombre": "Tecnología Espacial"}
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

# Rutas de la aplicación

@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')

        user = users_collection.find_one({"username": username})
        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('mensajeria'))
        else:
            return render_template('login.html', error="Credenciales inválidas.")
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        data = request.form
        error = validar_usuario(data)
        if error:
            return render_template('registro.html', error=error)

        if users_collection.find_one({"username": data['username']}):
            return render_template('registro.html', error="El nombre de usuario ya existe.")

        user = {
            "username": data['username'],
            "correo": data['correo'],
            "nombre": data['nombre'],
            "edad": data['edad'],
            "topicos_interes": data['topicos_interes'],
            "password": data['password'],
            "created_at": datetime.datetime.now()
        }
        users_collection.insert_one(user)
        session['username'] = data['username']
        return redirect(url_for('mensajeria'))
    topicos = list(topics_collection.find({}, {"_id": 0, "nombre": 1}))
    return render_template('registro.html', topicos=[t["nombre"] for t in topicos])

@app.route('/mensajeria')
def mensajeria():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('mensajeria.html', username=session['username'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('inicio'))

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

    if not users_collection.find_one({"username": sender}):
        return jsonify({"error": "El remitente no existe."}), 404

    if community:
        if not communities_collection.find_one({"name": community}):
            return jsonify({"error": "La comunidad no existe."}), 404
    else:
        if not users_collection.find_one({"username": receiver}):
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

@app.route('/mensajes/directo', methods=['GET'])
def obtener_mensajes_directo():
    """
    Obtiene el historial de mensajes entre dos usuarios.
    """
    sender = request.args.get('sender')
    receiver = request.args.get('receiver')

    if not sender or not receiver:
        return jsonify({"error": "Debe proporcionar el remitente y el destinatario."}), 400

    mensajes = list(messages_collection.find({
        "sender": {"$in": [sender, receiver]},
        "receiver": {"$in": [sender, receiver]},
        "community": None
    }).sort("timestamp", 1))

    return jsonify(mensajes), 200

@app.route('/mensajes/comunidad', methods=['GET'])
def obtener_mensajes_comunidad():
    """
    Obtiene el historial de mensajes de una comunidad.
    """
    community = request.args.get('community')

    if not community:
        return jsonify({"error": "Debe proporcionar el nombre de la comunidad."}), 400

    mensajes = list(messages_collection.find({
        "community": community
    }).sort("timestamp", 1))

    return jsonify(mensajes), 200

@app.route('/topicos', methods=['GET'])
def obtener_topicos():
    """
    Obtiene la lista de tópicos.
    """
    topicos = list(topics_collection.find({}, {"_id": 0, "nombre": 1}))
    return jsonify([t["nombre"] for t in topicos]), 200

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

    community = {
        "name": name,
        "description": description,
        "topicos": topicos_ids,
        "created_at": datetime.datetime.now()
    }
    communities_collection.insert_one(community)
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

# Manejo de errores
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    try:
        app.run(debug=True)
    except Exception as e:
        print(f"An error occurred: {e}")

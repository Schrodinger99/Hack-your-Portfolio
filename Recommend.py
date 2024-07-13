from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from surprise import dump
import pandas as pd

def Recommend(user_id):

    # Accecing MongoDB Atlas Cluster

    uri = "mongodb+srv://ivancz:nlZhpOlsRRlZq3pV@cluster0.nq3x0sh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

    client = MongoClient(uri, server_api = ServerApi('1'))

    # Accesing Database

    db = client["Platform"]
    user_db = db["users"]

    topics_db = [
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

    topics_df = pd.DataFrame(topics_db)

    users_id = []
    users_topics_of_interest = []

    users = list(user_db.find())
    for user in users:
        users_id.append(user["username"]) 

    for user in users:
        users_topics_of_interest.append(user["topicos_interes"])

    new_users_id = []
    new_topics_id = []
    interest = []

    for i in range(len(users_topics_of_interest)):
        for j in range(len(users_topics_of_interest[i])):
            new_users_id.append(users_id[i])
            interest.append(users_topics_of_interest[i][j])
            new_topics_id.append(j+1)

    topics_interest_df = pd.DataFrame({'user_id': new_users_id, 'topic_id': new_topics_id, 'interest': interest})

    # Function to recommend top-N topics for a user
    def recommend_topics_for_user(user_id, algo, n=10):
        # Get all topic IDs
        all_topic_ids = topics_interest_df['topic_id'].unique()

        # Predict interest levels for all topics for the user
        predictions = [algo.predict(user_id, topic_id) for topic_id in all_topic_ids]

        # Sort predictions by estimated interest level (est) in descending order
        recommendations = sorted(predictions, key=lambda x: x.est, reverse=True)[:n]

        return recommendations

    _, loaded_algorithm = dump.load('svd_rec_engine')

    # Example usage: Recommend topics for user 1
    

    top_n_recommendations = recommend_topics_for_user(user_id, loaded_algorithm, n=15)

    # Print top-N recommended topics

    print(f"Top {len(top_n_recommendations)} topics recommended for user {user_id}:")
    for recommendation in top_n_recommendations:
        id = round(recommendation.iid)
        recommended_topic = topics_df.set_index('id').loc[id, 'nombre']
        print(f"Topic: {recommended_topic}, Topic ID: {recommendation.iid}, Predicted Interest Level: {recommendation.est}")

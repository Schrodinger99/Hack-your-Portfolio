from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from surprise import dump
import pandas as pd

def Recommend(username):

    # Accecing MongoDB Atlas Cluster

    uri = "mongodb+srv://ivancz:nlZhpOlsRRlZq3pV@cluster0.nq3x0sh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

    client = MongoClient(uri, server_api = ServerApi('1'))

    # Accesing Database

    db = client["Platform"]
    user_db = db["users"]
    communities_db = db["communities"]

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
    communities_topics = []

    users = list(user_db.find())
    for user in users:
        users_id.append(user["username"]) 

    for user in users:
        users_topics_of_interest.append(user["topicos_interes"])
    
    communities = list(communities_db.find())
    for community in communities:
        communities_topics.append({"community_name" : community["nombre"], "topics" : community["topicos"]})

    new_users_id = []
    new_topics_id = []
    interest = []

    for i in range(len(users_topics_of_interest)):
        for j in range(len(users_topics_of_interest[i])):
            new_users_id.append(users_id[i])
            interest.append(users_topics_of_interest[i][j])
            new_topics_id.append(j+1)

    topics_interest_df = pd.DataFrame({'user_id': new_users_id, 'topic_id': new_topics_id, 'interest': interest})

    # Loading trained model
    _, loaded_algorithm = dump.load('svd_rec_engine')

    # Function to recommend top-N topics for a user
    def recommend_topics_for_user(user_id, algo, n=10):
        # Get all topic IDs
        all_topic_ids = topics_interest_df['topic_id'].unique()

        # Predict interest levels for all topics for the user
        predictions = [algo.predict(user_id, topic_id) for topic_id in all_topic_ids]

        # Sort predictions by estimated interest level (est) in descending order
        recommendations = sorted(predictions, key=lambda x: x.est, reverse=True)[:n]

        return recommendations

    # Example usage: Recommend topics for user 1
    
    top_n_recommendations = recommend_topics_for_user(username, loaded_algorithm, n=10)

    # Print top-N recommended topics

    user = user_db.find_one({"username": username}, {"_id": 0, "username": 1, "nombre": 1})
    user_name = user["nombre"]
    recommended_communities = []

    print(f"Top {len(top_n_recommendations)} topics recommended for user {user_name}:")
    for recommendation in top_n_recommendations:
        id = round(recommendation.iid)
        recommended_topic = topics_df.set_index('id').loc[id, 'nombre']
        for community in communities_topics:
            if recommended_topic in community["topics"]:
                if community["community_name"] not in recommended_communities:
                    recommended_communities.append(community["community_name"])
                
    return recommended_communities
    
    
    

Recommend("usuario1")

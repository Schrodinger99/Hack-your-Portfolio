from pymongo import MongoClient
from surprise import dump
import pandas as pd

def Recommend(username):
    # Accessing MongoDB Atlas Cluster
    uri = "mongodb+srv://ivancz:nlZhpOlsRRlZq3pV@cluster0.nq3x0sh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(uri)

    # Accessing Database
    db = client["Platform"]
    user_db = db["users"]
    communities_db = db["communities"]

    # Define topics (since topics_db is static, we can define it directly)
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

    # Fetch user data and topics of interest
    users = list(user_db.find())
    users_id = [user["username"] for user in users]
    users_topics_of_interest = [user["topicos_interes"] for user in users]

    # Fetch communities and their topics
    communities = list(communities_db.find())
    communities_topics = [{"community_name": community["nombre"], "topics": community["topicos"]} for community in communities]

    # Create DataFrame for user interests
    new_users_id = []
    new_topics_id = []
    interest = []

    for i, topics_of_interest in enumerate(users_topics_of_interest):
        for j, topic_id in enumerate(topics_of_interest):
            new_users_id.append(users_id[i])
            interest.append(topic_id)
            new_topics_id.append(j + 1)

    topics_interest_df = pd.DataFrame({'user_id': new_users_id, 'topic_id': new_topics_id, 'interest': interest})

    # Loading trained model
    _, loaded_algorithm = dump.load('svd_rec_engine')

    # Function to recommend top-N topics for a user
    def recommend_topics_for_user(user_id, algo, n=10):
        # Get all unique topic IDs
        all_topic_ids = topics_interest_df['topic_id'].unique()

        # Predict interest levels for all topics for the user
        predictions = [algo.predict(user_id, topic_id) for topic_id in all_topic_ids]

        # Sort predictions by estimated interest level (est) in descending order
        recommendations = sorted(predictions, key=lambda x: x.est, reverse=True)[:n]

        return recommendations

    # Example usage: Recommend topics for the given username
    top_n_recommendations = recommend_topics_for_user(username, loaded_algorithm, n=10)

    # Print top-N recommended topics
    print(f"Top {len(top_n_recommendations)} topics recommended for user {username}:")
    for recommendation in top_n_recommendations:
        id = round(recommendation.iid)
        recommended_topic = topics_df.set_index('id').loc[id, 'nombre']
        print(f"Topic: {recommended_topic}, Topic ID: {recommendation.iid}, Predicted Interest Level: {recommendation.est}")

    # Find communities related to the recommended topics
    recommended_communities = []
    for recommendation in top_n_recommendations:
        id = round(recommendation.iid)
        recommended_topic = topics_df.set_index('id').loc[id, 'nombre']
        for community in communities_topics:
            if recommended_topic in community["topics"] and community["community_name"] not in recommended_communities:
                recommended_communities.append(community["community_name"])

    return recommended_communities




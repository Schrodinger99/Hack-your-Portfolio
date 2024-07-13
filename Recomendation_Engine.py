from surprise import dump
import pandas as pd
import json

# Loading JSON files
with open('usuarios.json') as f:
    user_db = json.load(f)

with open('comunidades.json') as f:
    communities_db = json.load(f)

with open('topicos.json') as f:
    topics_db = json.load(f)

# Changing JSON into DataFrame
user_df = pd.DataFrame(user_db)
communities_df = pd.DataFrame(communities_db)
topics_df = pd.DataFrame(topics_db)

# Creating a table with the levels of interest individually
users_id = user_df['username'].unique()
users_topics_of_interest = user_df['topicos_interes']


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
user_id = 1
top_n_recommendations = recommend_topics_for_user(user_id, loaded_algorithm, n=15)

# Print top-N recommended topics

print(f"Top {len(top_n_recommendations)} topics recommended for user {user_id}:")
for recommendation in top_n_recommendations:
    id = round(recommendation.iid)
    recommended_topic = topics_df.set_index('id').loc[id, 'nombre']
    print(f"Topic: {recommended_topic}, Topic ID: {recommendation.iid}, Predicted Interest Level: {recommendation.est}")

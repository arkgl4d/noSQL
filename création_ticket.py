from faker import Faker
import random
import datetime
import redis
from pymongo import MongoClient
 
# Configuration of Faker
fake = Faker()
 
# List of positions
postes = ["Développeur", "Ingénieur système", "Chef de projet",
          "Technicien support", "Analyste"]
 
# List of criticality levels
niveaux_criticite = ["Faible", "Moyenne", "Élevée", "Critique"]
 
# Function to generate a fake ticket (add "numero" to the dictionary)
def generate_ticket(i):
    nom = fake.first_name()
    prenom = fake.last_name()
    poste = random.choice(postes)
    cause = fake.sentence()
    objet = fake.sentence()
    niveau_criticite = random.choice(niveaux_criticite)
    date_creation = datetime.datetime.now()
 
    # Add "numero" key with the current loop index (i)
    return {
        "nom": nom,
        "prenom": prenom,
        "poste": poste,
        "cause": cause,
        "objet": objet,
        "niveau_criticité": niveau_criticite,
        "date_creation": date_creation,
        "numero": i  # Add "numero" key and assign the current loop index
    }
 
# Generation of 10 fake tickets
tickets = []
for i in range(10):
    tickets.append(generate_ticket(i))
 
# Connect to Redis database
r = redis.Redis(host='localhost', port=6379, db=0)
 
# Connect to MongoDB database
client = MongoClient('mongodb://localhost:27017/')
db = client['tickets_db']
tickets_collection = db['tickets']
 
# Add tickets to Redis database
for ticket in tickets:
    r.hset('tickets', ticket['numero'], str(ticket))
 
# Add tickets to MongoDB database
tickets_collection.insert_many(tickets)
 
# Display of tickets
for ticket in tickets:
    print(f"**Ticket {ticket['numero']}**")
    for key, value in ticket.items():
        print(f"{key}: {value}")
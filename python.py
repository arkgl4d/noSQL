import datetime
import pymongo
from faker import Faker
import random
import redis
import time
 
fake = Faker()
 
# Configuration
redis_host = "localhost"
redis_port = 6379
mongo_host = "localhost"
mongo_port = 27017
mongo_db = "tickets"
mongo_collection = "resolved_tickets"
 
# Connect to Redis
redis_client = redis.Redis(host=redis_host, port=redis_port)
 
# Connect to MongoDB
try:
    mongo_client = pymongo.MongoClient(f"mongodb://{mongo_host}:{mongo_port}/")
    db = mongo_client[mongo_db]
    collection = db[mongo_collection]
    print("Connected to MongoDB successfully!")
except pymongo.errors.ConnectionFailure as e:
    print("Could not connect to MongoDB:", e)
    exit()
 
def generate_ticket(i):
    nom = fake.first_name()
    prenom = fake.last_name()
    poste = random.choice(postes)
    cause = fake.sentence()
    objet = fake.sentence()
    niveau_criticite = random.choice(niveaux_criticite)
    date_creation = datetime.datetime.now()
    etat = "nouveau"
    ticket = {
        "nom": nom,
        "prenom": prenom,
        "poste": poste,
        "cause": cause,
        "objet": objet,
        "niveau_criticité": niveau_criticite,
        "date_creation": date_creation.isoformat(),
        "numero": i,
        "etat": etat,
    }
    return ticket
 
# List of positions
postes = ["Développeur", "Ingénieur système", "Chef de projet", "Technicien support", "Analyste"]
 
# List of criticality levels
niveaux_criticite = ["Faible", "Moyenne", "Élevée", "Critique"]
 
# List of states
etats = ["attribué", "nouveau", "clôturé", "résolu"]
 
# Generate and store tickets in Redis (temporary storage)
tickets = []
for i in range(10):
    ticket = generate_ticket(i)
    tickets.append(ticket)
    redis_client.hmset(f"ticket_{ticket['numero']}", ticket)
 
def update_ticket_state(ticket_number, new_state):
    print(f"Attempting to update ticket {ticket_number} to state '{new_state}' in MongoDB...")
    ticket_data = redis_client.hgetall(f"ticket_{ticket_number}")
    if ticket_data:
        ticket = {key.decode("utf-8"): value.decode("utf-8") for key, value in ticket_data.items()}
        if new_state in ["résolu", "clôturé"]:
            ticket["etat"] = new_state
            del ticket["numero"]
            collection.insert_one(ticket)
            redis_client.delete(f"ticket_{ticket_number}")
            print(f"Ticket {ticket_number} finalized and stored in MongoDB.")
 
            # Remove the ticket from the global tickets list
            global tickets
            tickets = [t for t in tickets if t["numero"] != ticket_number]
        else:
            print(f"Ticket {ticket_number} not found in Redis or no update needed.")
 
# Function to finalize ticket (move from Redis to MongoDB)
def finalize_ticket(ticket_number):
    ticket_data = redis_client.hgetall(f"ticket_{ticket_number}")
    if ticket_data:
        ticket = {key.decode("utf-8"): value.decode("utf-8") for key, value in ticket_data.items()}
        if ticket["etat"] in ["résolu", "clôturé"]:
            del ticket["numero"]
            collection.insert_one(ticket)
            redis_client.delete(f"ticket_{ticket_number}")
            print(f"Ticket {ticket_number} finalized and stored in MongoDB.")
 
# Monitor Redis for ticket state changes
while True:
    for ticket in tickets:
        current_state = redis_client.hget(f"ticket_{ticket['numero']}", "etat")
        if current_state is not None:
            current_state = current_state.decode("utf-8")
        else:
            print(f"Ticket {ticket['numero']} not found in Redis.")
            continue
 
        if current_state != ticket["etat"]:
            if current_state == "attribué":
                print(f"Ticket {ticket['numero']} state changed to '{current_state}'. Keeping it in Redis.")
            else:
                update_ticket_state(ticket["numero"], current_state)
    time.sleep(1)
 
 
# Close connections
redis_client.close()
mongo_client.close()
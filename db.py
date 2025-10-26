from pymongo import MongoClient

# yaha apna Mongo URL daalo
MONGO_URL = "mongodb+srv://sufyan532011:2011@bey-wars.oji9phy.mongodb.net/?retryWrites=true&w=majority&appName=Bey-Wars"

client = MongoClient(MONGO_URL)
db = client["metube"]   # Database ka naam jo aapne banaya
users = db["users"]# Example collection
channels = db["channels"]
videos = db["videos"]
def generate_channel_id():
    import random, string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

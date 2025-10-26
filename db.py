from pymongo import MongoClient

# yaha apna Mongo URL daalo
MONGO_URL = "mongodb+srv://username:password@cluster0.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_URL)
db = client["metube"]   # Database ka naam jo aapne banaya
users = db["users"]# Example collection
channels = db["channels"]
videos = db["videos"]

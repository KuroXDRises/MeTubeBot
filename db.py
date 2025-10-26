from pymongo import MongoClient

# yaha apna Mongo URL daalo
MONGO_URL = "mongodb://sufyan532011:5042@auctionbot.5ms20.mongodb.net/?retryWrites=true&w=majority&appName=AuctionBot"

client = MongoClient(MONGO_URL)
db = client["metube"]   # Database ka naam jo aapne banaya
users = db["users"]# Example collection
channels = db["channels"]
videos = db["videos"]

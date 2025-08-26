from config import mongodb_connection_string
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import CollectionInvalid
import redis
from datetime import timedelta


client: MongoClient = MongoClient(mongodb_connection_string, server_api=ServerApi('1'))



# --------------------------------------------- redis connection ---------------------------------------------
# REDIS_HOST = get_settings().redis_host
# REDIS_PORT = get_settings().redis_port
# REDIS_PASSWORD = get_settings().redis_password
# REDIS_EXPIRE = timedelta(minutes=5)  # Cache expiration time

# Initialize Redis client
# def get_redis_client():
#     try:
#         # production cache
#         # redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, username="default", password=REDIS_PASSWORD)

#         # local cache
#         redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

#         redis_client.ping()  # Check connection
#         print("Connected to Redis")
#     except redis.exceptions.ConnectionError as e:
#         print(f"Error connecting to Redis: {e}")
#         redis_client = None  # Disable caching if Redis is not available
    
#     yield redis_client



# --------------------------------------------- mongo connection ---------------------------------------------
def get_db():
    """
    Establishes a connection to VIT MongoDB database.

    This function attempts to connect to the MongoDB server and retrieve
    VIT database. It checks the server's connectivity by 
    pinging it, and raises an exception if the connection fails.

    Returns:
        Database: The 'VIT' MongoDB database instance.

    Raises:
        Exception: If there is an error connecting to MongoDB.
    """
    try:
        # ping the server to check connectivity
        client.server_info()
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        db = client['vit']
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise e


db = get_db()

collection_names = [
    'users',
    'chats',
    'messages',
    'faqs',
    'error_logs',    
]

for collection_name in collection_names:
    try:
        db.create_collection(collection_name, check_exists=True,)
        print(collection_name, "collection created")
    except CollectionInvalid:
        print("Collection already exists. Skipping creation.")


users_collection = db['users']
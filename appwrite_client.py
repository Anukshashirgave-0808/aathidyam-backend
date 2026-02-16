import os
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.databases import Databases

load_dotenv()  # auto loads .env

endpoint = os.getenv("APPWRITE_ENDPOINT")
project_id = os.getenv("APPWRITE_PROJECT_ID")
api_key = os.getenv("APPWRITE_API_KEY")

if not endpoint or not project_id or not api_key:
    raise Exception("❌ Appwrite ENV variables missing")

client = Client()
client.set_endpoint(endpoint)
client.set_project(project_id)
client.set_key(api_key)

databases = Databases(client)

import os
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.tables_db import TablesDB


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

# Legacy Service
databases = Databases(client)

# Modern Service (v16+)
tablesDB = TablesDB(client)

def _safe_get(data, key, default=None):
    """
    Robust attribute/key getter for Appwrite SDK v16 responses.
    Handles Row objects (data in .data dict) and legacy Document objects.
    """
    if data is None:
        return default

    # CASE 1: Data is a plain dictionary (standard SDK output or manually parsed)
    if isinstance(data, dict):
        # Alias $id <-> id
        if key == 'id' and 'id' not in data and '$id' in data:
            return data.get('$id')
        if key == '$id' and '$id' not in data and 'id' in data:
            return data.get('id')
        
        # Alias rows <-> documents
        if key == 'documents' and 'documents' not in data and 'rows' in data:
            return data.get('rows')
        if key == 'rows' and 'rows' not in data and 'documents' in data:
            return data.get('documents')

        return data.get(key, default)

    # CASE 2: SDK Row object (Appwrite v16) — actual data lives in .data dict
    row_data = getattr(data, 'data', None)
    if isinstance(row_data, dict):
        if key == '$id':
            val = row_data.get('$id') or getattr(data, 'id', None)
            return val if val is not None else default
        if key in row_data:
            return row_data[key]
        # Fallback to top-level metadata (id, tableId, etc.)
        top_val = getattr(data, key, None)
        return top_val if top_val is not None else default

    # CASE 3: Legacy SDK Objects or Root List Objects (RowList / DocumentList)
    val = getattr(data, key, None)
    if val is None:
        if key == 'documents': val = getattr(data, 'rows', None)
        elif key == 'rows': val = getattr(data, 'documents', None)
        elif key == 'id': val = getattr(data, '$id', None)
        elif key == '$id': val = getattr(data, 'id', None)

    return val if val is not None else default

from dotenv import load_dotenv
import os

load_dotenv()
CONN_URI_SLP = os.environ.get('CONN_URI_SLP')
DB_NAME_SLP = os.environ.get('DB_NAME_SLP')
MAPQUEST_API_KEY = os.environ.get('MAPQUEST_API_KEY')

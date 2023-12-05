from dotenv import load_dotenv
import os

load_dotenv()
CONN_URI_SLP = os.environ.get('CONN_URI_SLP')
DB_NAME_SLP = os.environ.get('DB_NAME_SLP')
MAPQUEST_API_KEY = os.environ.get('MAPQUEST_API_KEY')
SUBJECTIVE_GRADING_API = os.environ.get('SUBJECTIVE_GRADING_API')
PINECONE_INDEXING_API=os.environ.get('PINECONE_INDEXING_API')
OPENAI_KEY=os.environ.get('OPENAI_KEY')


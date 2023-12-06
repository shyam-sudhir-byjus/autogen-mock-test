from dotenv import load_dotenv
import os

load_dotenv()
CONN_URI_SLP = os.environ.get('CONN_URI_SLP')
DB_NAME_SLP = os.environ.get('DB_NAME_SLP')
MAPQUEST_API_KEY = os.environ.get('MAPQUEST_API_KEY')
SUBJECTIVE_GRADING_API = os.environ.get('SUBJECTIVE_GRADING_API')
PINECONE_INDEXING_API=os.environ.get('PINECONE_INDEXING_API')
OPENAI_KEY=os.environ.get('OPENAI_KEY')
MATHPIX_APP_ID=os.environ.get('MATHPIX_APP_ID')
MATHPIX_APP_KEY=os.environ.get('MATHPIX_APP_KEY')
GOOGLE_API_KEY=os.environ.get('GOOGLE_API_KEY')
OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY')
OPENAI_BASE_KEY=os.environ.get('OPENAI_BASE_KEY')
OPENAI_API_VERSION=os.environ.get('OPENAI_API_VERSION')
OPENAI_API_TYPE=os.environ.get('OPENAI_API_TYPE')
CHAT_COMPLETION_MODEL=os.environ.get('CHAT_COMPLETION_MODEL')






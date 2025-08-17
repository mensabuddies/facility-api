import os

from dotenv import load_dotenv, find_dotenv

# Local / in test, use .env files - but not for the docker build
production_environment = os.getenv("PRODUCTION_ENVIRONMENT", False)

if not production_environment:
    load_dotenv(find_dotenv())
    load_dotenv(find_dotenv(filename=".env.local"), override=True)

db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
db_url = os.getenv("DB_URL")
db_name = os.getenv("DB_NAME")
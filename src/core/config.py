import os
from pydantic_settings import BaseSettings

# Load the .env.dev file if it exists, for local development
from dotenv import load_dotenv
if os.path.exists(".env.dev"):
    load_dotenv(".env.dev")


class Settings(BaseSettings):
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = False

    # Azure Storage
    AZURE_STORAGE_CONNECTION_STRING: str
    BLOB_CONTAINER_NAME: str = "pdf-uploads"

    # Azure Cosmos DB
    AZURE_COSMOS_MONGO_CONNECTION_STRING: str    
    COSMOS_DATABASE_NAME: str = "JobDatabase"
    COSMOS_CONTAINER_NAME: str = "JobContainer"

    class Config:
        case_sensitive = True

settings = Settings()
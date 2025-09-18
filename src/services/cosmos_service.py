# src/services/cosmos_service.py
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

from src.core.config import settings
from src.models.job import JobCreate, JobInDB

logger = logging.getLogger(__name__)

class CosmosDBService:
    def __init__(self, client: AsyncIOMotorClient):
        self.client = client
        # In MongoDB terms, a container is a collection
        self.database = self.client[settings.COSMOS_DATABASE_NAME]
        self.collection = self.database[settings.COSMOS_CONTAINER_NAME]

    @classmethod
    def connect(cls):
        logger.info("Connecting to Cosmos DB for MongoDB...")
        try:
            # The Cosmos DB Mongo API requires specific settings
            client = AsyncIOMotorClient(
                settings.AZURE_COSMOS_MONGO_CONNECTION_STRING,
                # Recommended settings for Cosmos DB
                maxPoolSize=200, 
                minPoolSize=20,
                serverSelectionTimeoutMS=30000
            )
            # The ismaster command is cheap and does not require auth.
            client.admin.command('ismaster')
            logger.info("Cosmos DB for MongoDB client created and connection validated.")
            return cls(client)
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to Cosmos DB for MongoDB: {e}", exc_info=True)
            raise

    async def initialize(self):
        """
        Initialization is less critical for MongoDB as databases and collections
        are often created on first use. This method is kept for structural consistency.
        """
        logger.info("Cosmos DB for MongoDB service is ready.")
        # You could add logic here to create indexes if needed
        # Example: await self.collection.create_index([("id", 1)], unique=True)
        pass

    def close(self):
        logger.info("Closing Cosmos DB for MongoDB client.")
        self.client.close()

    async def create_job(self, job_data: JobCreate) -> JobInDB:
        logger.info(f"Creating job record for job_id: {job_data.id}")
        # MongoDB uses '_id' by default, but we use 'id' in our model.
        # We need to map it. We also remove partitionKey as it's a SQL API concept.
        doc_to_insert = job_data.model_dump()
        doc_to_insert["_id"] = doc_to_insert.pop("id")
        doc_to_insert.pop("partitionKey", None) # Safely remove if exists
        
        await self.collection.insert_one(doc_to_insert)
        return JobInDB(**job_data.model_dump())

    async def get_job_by_id(self, job_id: str) -> Optional[JobInDB]:
        logger.info(f"Fetching job with id: {job_id}")
        doc = await self.collection.find_one({"_id": job_id})
        if doc:
            # Map '_id' back to 'id' for our Pydantic model
            doc["id"] = doc.pop("_id")
            # For compatibility with JobInDB, add a placeholder partitionKey
            doc["partitionKey"] = doc["id"]
            return JobInDB(**doc)
        
        logger.warning(f"Job with id '{job_id}' not found.")
        return None
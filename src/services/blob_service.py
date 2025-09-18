import logging
from azure.storage.blob.aio import BlobServiceClient

from src.core.config import settings

logger = logging.getLogger(__name__)

class BlobStorageService:
    def __init__(self, client: BlobServiceClient):
        self.client = client
        self.container_client = None

    @classmethod
    def connect(cls):
        logger.info("Connecting to Azure Blob Storage...")
        client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        logger.info("Blob Storage client created.")
        return cls(client)

    async def initialize(self):
        """Idempotently create the blob container."""
        try:
            logger.info(f"Getting or creating blob container: '{settings.BLOB_CONTAINER_NAME}'")
            self.container_client = self.client.get_container_client(settings.BLOB_CONTAINER_NAME)
            if not await self.container_client.exists():
                await self.container_client.create_container()
            logger.info("Blob Storage container initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Blob Storage container: {e}", exc_info=True)
            raise

    async def close(self):
        logger.info("Closing Blob Storage client.")
        await self.client.close()

    async def upload_file(self, file_content: bytes, doc_id: str, metadata: dict) -> str:
        blob_client = self.container_client.get_blob_client(doc_id)
        logger.info(f"Uploading blob '{doc_id}' with metadata: {metadata}")
        await blob_client.upload_blob(file_content, overwrite=True, metadata=metadata)
        return blob_client.url
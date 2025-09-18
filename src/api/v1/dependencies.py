# src/api/dependencies.py

from fastapi import Request
from src.services.blob_service import BlobStorageService
from src.services.cosmos_service import CosmosDBService

# These functions provide the service instances stored in the app's state.

def get_cosmos_service(request: Request) -> CosmosDBService:
    """Dependency injector for CosmosDBService."""
    return request.app.state.cosmos_service

def get_blob_service(request: Request) -> BlobStorageService:
    """Dependency injector for BlobStorageService."""
    return request.app.state.blob_service
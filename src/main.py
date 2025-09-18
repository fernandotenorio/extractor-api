import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from src.api.v1.endpoints.extraction import router as extraction_router
from src.services.blob_service import BlobStorageService
from src.services.cosmos_service import CosmosDBService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application startup...")
    app.state.cosmos_service = CosmosDBService.connect()
    await app.state.cosmos_service.initialize()
    
    app.state.blob_service = BlobStorageService.connect()
    await app.state.blob_service.initialize()
    
    yield
    
    # Shutdown
    logger.info("Application shutdown...")
    if hasattr(app.state, 'cosmos_service') and app.state.cosmos_service:
        await app.state.cosmos_service.close()
    if hasattr(app.state, 'blob_service') and app.state.blob_service:
        await app.state.blob_service.close()

app = FastAPI(
    title="Document Extraction API",
    description="An API to upload documents for processing.",
    version="1.0.0",
    lifespan=lifespan
)

# --- API Routers ---
app.include_router(extraction_router, prefix="/api/v1/extraction", tags=["Extraction"])

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
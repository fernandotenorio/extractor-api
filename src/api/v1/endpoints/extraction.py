import uuid
import logging
from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Query

from src.models.job import JobCreate, JobUploadResponse, JobStatusResponse, JobStatus
from src.services.blob_service import BlobStorageService
from src.services.cosmos_service import CosmosDBService
from src.api.dependencies import get_blob_service, get_cosmos_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload", response_model=List[JobUploadResponse], status_code=status.HTTP_202_ACCEPTED)
async def upload_documents(
    files: List[UploadFile] = File(..., description="One or more PDF documents to upload."),
    cosmos_service: CosmosDBService = Depends(get_cosmos_service),
    blob_service: BlobStorageService = Depends(get_blob_service)
):
    """
    Uploads multiple PDF documents, creates a job record for each,
    and uploads them to Azure Blob Storage.
    """
    response_data = []

    for file in files:
        if not file.filename:
            # This case is unlikely with FastAPI but good to have
            continue

        job_id = str(uuid.uuid4())
        doc_id = str(uuid.uuid4())
        
        # 1. Create the job record in Cosmos DB first
        job_to_create = JobCreate(
            id=job_id,
            partitionKey=job_id, # Use job_id as partition key for efficient lookups
            doc_id=doc_id,
            doc_name=file.filename,
            status=JobStatus.WAITING
        )
        job_record = await cosmos_service.create_job(job_to_create)

        # 2. Upload file to Blob Storage with metadata pointing to the job
        try:
            file_content = await file.read()
            blob_metadata = {
                "job_id": job_record.id,
                "doc_id": job_record.doc_id,
                "original_filename": job_record.doc_name
            }
            await blob_service.upload_file(file_content, doc_id, blob_metadata)
            logger.info(f"Successfully uploaded {file.filename} as doc_id {doc_id} for job_id {job_id}")
            response_data.append(JobUploadResponse(**job_record.model_dump()))

        except Exception as e:
            logger.error(f"Failed to upload {file.filename} for job {job_id}: {e}", exc_info=True)
            # If upload fails, we could update the job status to 'upload_failed'
            # For simplicity here, we will just return a different status in the response.
            # A more robust implementation would update the Cosmos record.
            response_data.append(JobUploadResponse(
                id=job_id,
                doc_id=doc_id,
                doc_name=file.filename,
                status=JobStatus.UPLOAD_FAILED
            ))
        finally:
            await file.close()

    return response_data


@router.get("/job-status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str = Query(..., description="The ID of the job to check."),
    cosmos_service: CosmosDBService = Depends(get_cosmos_service)
):
    """
    Retrieves the status and processed data for a given job ID.
    """
    job_data = await cosmos_service.get_job_by_id(job_id)
    if job_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )
    return JobStatusResponse(**job_data.model_dump())
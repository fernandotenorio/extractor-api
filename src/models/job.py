from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid

class JobStatus(str, Enum):
    WAITING = "waiting"
    PROCESSING = "processing"
    DONE = "done"
    UPLOAD_FAILED = "upload_failed"
    PROCESSING_FAILED = "failed"

class JobBase(BaseModel):
    doc_id: str = Field(..., description="Unique identifier for the document.")
    doc_name: str = Field(..., description="Original name of the document.")
    status: JobStatus = Field(JobStatus.WAITING, description="Current status of the job.")

class JobCreate(JobBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique job ID, also the item ID in Cosmos.")
    # In Cosmos DB, it's good practice to have a partition key. For this simple app,
    # we can use the job ID itself, ensuring good distribution.
    partitionKey: str 

class JobInDB(JobCreate):
    processed_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class JobUploadResponse(BaseModel):
    job_id: str = Field(..., alias="id")
    doc_id: str
    doc_name: str
    status: JobStatus

    class Config:
        populate_by_name = True
        
class JobStatusResponse(JobInDB):
    job_id: str = Field(..., alias="id")
    
    class Config:
        populate_by_name = True
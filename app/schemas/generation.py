from pydantic import BaseModel
from typing import Optional


class GenerationRequest(BaseModel):
    project_id: str
    prompt: str
    negative_prompt: Optional[str] = None
    
    
class GenerationResponse(BaseModel):
    job_id: str
    status: str
    message: str
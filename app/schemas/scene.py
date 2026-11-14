from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class SceneObjectCreate(BaseModel):
    object_type: str
    display_name: str
    color: Optional[str] = None
    material: Optional[str] = None
    
class SceneObjectResponse(BaseModel):
    model_config= ConfigDict(from_attributes=True)
    id: str
    project_id: str
    object_type: str
    
    display_name: str
    color: Optional[str]
    material: Optional[str]
    created_at: datetime
    
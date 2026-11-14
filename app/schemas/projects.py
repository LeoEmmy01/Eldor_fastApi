from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class ProjectCreate(BaseModel):
    title: str
    image_filename: str = Field(pattern=r"^[a-f0-9]{32}\.(jpg|png|gif|webp)$")
    room_type: Optional[str] = "Living Room"
    style: Optional[str] = "Modern"
    primary_color: Optional[str] = "#FFFFFF"
    secondary_color: Optional[str] = "#000000"
    accent_color: Optional[str] = "#FF0000"
    
    
class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    title: str
    original_image_url: str
    room_type: Optional[str]
    style: Optional[str]
    primary_color: Optional[str]
    secondary_color: Optional[str]
    accent_color: Optional[str]
    created_at: datetime
    updated_at: datetime
    

        
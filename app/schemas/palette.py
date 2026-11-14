from typing import Optional

from pydantic import BaseModel, Field

HEX_COLOR = r"^#([A-Fa-f0-9]{6})$"


class PaletteUpdate(BaseModel):
    primary_color: Optional[str] = Field(None, pattern=HEX_COLOR)
    secondary_color: Optional[str] = Field(None, pattern=HEX_COLOR)
    accent_color: Optional[str] = Field(None, pattern=HEX_COLOR)


class PaletteResponse(BaseModel):
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
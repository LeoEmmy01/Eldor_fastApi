import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_image_url: Mapped[str] = mapped_column(Text, nullable=False)
    room_type: Mapped[str] = mapped_column(String(100), nullable=True)
    style: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # 3-Color Palette (HEX values)
    primary_color: Mapped[str] = mapped_column(String(7), nullable=True)
    secondary_color: Mapped[str] = mapped_column(String(7), nullable=True)
    accent_color: Mapped[str] = mapped_column(String(7), nullable=True)

    # Pass datetime.now without parentheses so it evaluates dynamically per row creation
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="projects")
    versions: Mapped[list["DesignVersion"]] = relationship("DesignVersion", back_populates="project", cascade="all, delete-orphan")
    jobs: Mapped[list["GenerationJob"]] = relationship("GenerationJob", back_populates="project", cascade="all, delete-orphan")
    scene_objects: Mapped[list["SceneObject"]] = relationship("SceneObject", back_populates="project", cascade="all, delete-orphan")
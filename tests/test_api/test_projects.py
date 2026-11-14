import asyncio
import importlib
import shutil
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.database.base import Base
from app.database.session import get_db

# Register all models on Base.metadata before create_all runs.
try:
    importlib.import_module("app.models")
except ImportError:
    pass


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    password = "Secret123!"

    r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert r.status_code in (200, 201), f"register failed: {r.status_code} {r.text}"

    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"

    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ----------------------------- Tests -----------------------------

def test_app_loads(client):
    assert client.get("/docs").status_code == 200


def test_database_tables_created():
    assert len(Base.metadata.tables) > 0


def test_projects_require_auth(client):
    # Confirms the 401 you saw is intentional
    assert client.get("/api/v1/projects/").status_code == 401


def test_list_projects(client, auth_headers):
    r = client.get("/api/v1/projects/", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_create_project(client, auth_headers):
    from app.api.v1.endpoints.uploads import storage

    upload = client.post(
        "/api/v1/upload",
        headers=auth_headers,
        files={"file": ("room.jpg", b"\xff\xd8\xffroom-image", "image/jpeg")},
    )
    assert upload.status_code == 200, upload.text

    r = client.post(
        "/api/v1/projects/",
        headers=auth_headers,
        json={
            "title": "Test Project",
            "image_filename": upload.json()["filename"],
            "room_type": "living room",
            "style": "modern",
        },
    )
    assert r.status_code in (200, 201), r.text
    assert r.json()["title"] == "Test Project"
    asyncio.run(storage.delete_file(f"uploads/{r.json()['user_id']}/{upload.json()['filename']}"))


def test_generation_job_runs_configured_workflow(client, auth_headers, monkeypatch, tmp_path):
    from app.api.v1.endpoints.uploads import storage
    from app.core.config import settings

    upload = client.post(
        "/api/v1/upload",
        headers=auth_headers,
        files={"file": ("room.jpg", b"\xff\xd8\xffroom-image", "image/jpeg")},
    )
    assert upload.status_code == 200, upload.text
    project = client.post(
        "/api/v1/projects/",
        headers=auth_headers,
        json={"title": "Workflow Project", "image_filename": upload.json()["filename"]},
    )
    assert project.status_code == 200, project.text
    user_id = project.json()["user_id"]
    filename = upload.json()["filename"]
    source_path = Path(settings.LOCAL_STORAGE_PATH).resolve() / "uploads" / user_id / filename
    temp_source = tmp_path / "uploads" / user_id / filename
    temp_source.parent.mkdir(parents=True)
    shutil.copyfile(source_path, temp_source)
    monkeypatch.setattr(settings, "LOCAL_STORAGE_PATH", str(tmp_path))

    from app.services import master_pipline

    class SuccessfulAnalysis:
        async def analyze_room(self, image_path):
            return {
                "success": True,
                "analysis_output": {
                    "room_type": "living room",
                    "furniture": ["sofa"],
                    "lighting": "natural",
                    "layout_notes": "open layout",
                    "dominant_colors": ["white"],
                },
            }

    class SuccessfulDepth:
        async def generate_depth_map(self, image_path, output_dir):
            return {"success": True, "depth_map_url": "depth.png"}

    class SuccessfulSegmentation:
        async def generate_masks(self, image_path, output_dir):
            return {"success": True, "segmented_regions": []}

    async def generate_image(**kwargs):
        assert kwargs["user_id"] == project.json()["user_id"]
        assert kwargs["negative_prompt"] == "blurry"
        assert Path(kwargs["image_path"]).is_file()
        return {"success": True, "output_url": "/api/v1/files/result.png?kind=generations"}

    monkeypatch.setattr(master_pipline, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(master_pipline, "RoomUnderstandingPipeline", SuccessfulAnalysis)
    monkeypatch.setattr(master_pipline, "DepthEstimationPipeline", SuccessfulDepth)
    monkeypatch.setattr(master_pipline, "RoomSegmentationPipeline", SuccessfulSegmentation)
    monkeypatch.setattr(master_pipline.ai_orchestrator, "run_generation", generate_image)

    queued = client.post(
        "/api/v1/generations",
        headers=auth_headers,
        json={
            "project_id": project.json()["id"],
            "prompt": "Add warm lighting",
            "negative_prompt": "blurry",
        },
    )
    assert queued.status_code == 200, queued.text

    status_response = client.get(
        f"/api/v1/generations/{queued.json()['job_id']}",
        headers=auth_headers,
    )
    assert status_response.status_code == 200, status_response.text
    assert status_response.json()["status"] == "completed"
    assert status_response.json()["output_url"] == "/api/v1/files/result.png?kind=generations"
    asyncio.run(storage.delete_file(f"uploads/{user_id}/{filename}"))
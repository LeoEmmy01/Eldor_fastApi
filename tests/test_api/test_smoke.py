from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_docs_loads():
    assert client.get("/docs").status_code == 200
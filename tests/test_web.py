from fastapi.testclient import TestClient
from findex.web.app import app, get_index

class MockIndex:
    num_docs = 5
    avg_doc_length = 10.0
    
    def __len__(self):
        return 10
        
    def get_meta(self, doc_id: int):
        if doc_id == 9999:
            raise KeyError(f"Document {doc_id} not found")
        class Meta:
            def __init__(self, did: int):
                self.doc_id = did
                self.name = f"doc_{did}.txt"
                self.length = 10
        return Meta(doc_id)

app.dependency_overrides[get_index] = lambda: MockIndex()

client = TestClient(app)

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Findex Search" in response.text

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_document_not_found():
    response = client.get("/docs/9999")
    assert response.status_code == 404
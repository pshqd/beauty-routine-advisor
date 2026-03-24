from services.rag_service import RAGService

def test_rag_service_init():
    service = RAGService()
    assert service is not None

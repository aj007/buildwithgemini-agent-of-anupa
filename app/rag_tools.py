"""RAG Corpus retrieval module for TriCoach AI grounding.

EXPOSES RETRIEVAL AS A PLAIN FUNCTION TOOL:
Required by ADK so it coexists safely alongside other function tools.
"""

import vertexai
from vertexai.preview import rag

CORPUS_NAME = "projects/687482616499/locations/us-central1/ragCorpora/34858916647010304"


def consult_rag_corpus(query: str) -> str:
    """Searches the grounded knowledge corpus (e.g. Project Gutenberg texts and health/herbal literature)
    and returns matching relevant passages.

    Args:
        query: What topic, remedy, herb, or concept to search for in the corpus.

    Returns:
        Matched text passages from the grounded RAG corpus.
    """
    if not CORPUS_NAME:
        return "RAG corpus is currently initializing."

    try:
        vertexai.init(project="qwiklabs-gcp-01-44253ac8b396", location="us-central1")
        resp = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=CORPUS_NAME)],
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=5),
        )
        contexts = getattr(resp.contexts, "contexts", [])
        passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
        return "\n\n---\n\n".join(passages) or "No relevant passages found in corpus."
    except Exception as e:
        return f"RAG retrieval query error: {str(e)}"

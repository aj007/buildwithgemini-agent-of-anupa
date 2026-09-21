"""Script to create a Serverless Vertex AI RAG Corpus and index pg49513.txt."""

import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-01-44253ac8b396"
LOCATION = "us-central1"
GCS_PATH = "gs://tricoach-assets-44253ac8b396/rag/pg49513.txt"

PARSING_PROMPT = (
    "Extract useful botanical, health, fitness, and herbal facts described in this text. "
    "Ignore and omit all metadata, boilerplate, licensing, and image captions. "
    "Output clean, self-contained text."
)


def create_corpus():
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    print("1. Updating RAG engine config to serverless mode...")
    cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
    rag.update_rag_engine_config(
        rag_engine_config=rag.RagEngineConfig(
            name=cfg,
            rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
        )
    )

    print("2. Creating RAG corpus...")
    corpus = rag.create_corpus(
        display_name="tricoach-herbal-corpus",
        embedding_model_config=rag.EmbeddingModelConfig(
            publisher_model="publishers/google/models/text-embedding-005"
        ),
    )
    print(f"✅ Corpus created: {corpus.name}")

    print(f"3. Importing and indexing {GCS_PATH}...")
    resp = rag.import_files(
        corpus_name=corpus.name,
        paths=[GCS_PATH],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
        ),
        llm_parser=rag.LlmParserConfig(
            model_name="gemini-2.5-flash",
            custom_parsing_prompt=PARSING_PROMPT,
        ),
    )
    print(f"✅ Imported files count: {resp.imported_rag_files_count}")
    return corpus.name


if __name__ == "__main__":
    corpus_name = create_corpus()
    print(f"\nSAVE THIS CORPUS NAME:\n{corpus_name}")

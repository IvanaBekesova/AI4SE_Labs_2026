import json
import sys
from pathlib import Path

import numpy as np

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # 384-dimensional vectors
DEFAULT_CHUNKS = "../Task_2/chunks.json"
DEFAULT_STORE = "embeddings.json"

_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts):
    """Return L2-normalised embeddings (one row per text)."""
    vectors = get_model().encode(texts, normalize_embeddings=True,
                                 show_progress_bar=False)
    return np.asarray(vectors, dtype=np.float32)


def chunk_to_text(chunk):
    """What part of the chunk gets embedded: location + symbol names + code."""
    header = f"File: {chunk['file']}\n"
    if chunk.get("class"):
        header += f"Class: {chunk['class']}\n"
    header += f"Symbols: {', '.join(chunk.get('symbols', []))}\n\n"
    return header + chunk["content"]


def build(chunks_file=DEFAULT_CHUNKS, store_file=DEFAULT_STORE):
    chunks = json.loads(Path(chunks_file).read_text(encoding="utf-8"))
    vectors = embed_texts([chunk_to_text(c) for c in chunks])

    store = []
    for chunk, vec in zip(chunks, vectors):
        store.append({**chunk, "embedding": [round(float(x), 6) for x in vec]})

    Path(store_file).write_text(json.dumps(store, ensure_ascii=False), encoding="utf-8")
    print(f"{len(store)} chunk-embedding pairs ({vectors.shape[1]} dims) saved to {store_file}")


def main():
    build(*sys.argv[1:3])


if __name__ == "__main__":
    main()
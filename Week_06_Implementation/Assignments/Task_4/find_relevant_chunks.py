import json
import sys
from pathlib import Path

import numpy as np

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # must be the same model as in Task 3
DEFAULT_STORE = "../Task_3/embeddings.json"
DEFAULT_N = 5

_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_task(task):
    """Turn the input task into a normalised embedding (same model as the chunks)."""
    vec = get_model().encode([task], normalize_embeddings=True, show_progress_bar=False)[0]
    return np.asarray(vec, dtype=np.float32)


def load_store(store_file=DEFAULT_STORE):
    """Load chunk-embedding pairs and stack the embeddings into one matrix."""
    store = json.loads(Path(store_file).read_text(encoding="utf-8"))
    matrix = np.array([item["embedding"] for item in store], dtype=np.float32)
    return store, matrix


def retrieve(task, n=DEFAULT_N, store_file=DEFAULT_STORE):
    """Return the n chunks whose embeddings are most similar to the task embedding.

    Similarity = cosine similarity. All vectors are normalised, so it equals
    the dot product, computed for all chunks at once as a matrix-vector product.
    """
    store, matrix = load_store(store_file)
    query = embed_task(task)
    scores = matrix @ query
    best = np.argsort(-scores)[:n]
    return [{"score": float(scores[i]), **{k: v for k, v in store[i].items()
                                           if k != "embedding"}}
            for i in best]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    task = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_N
    store_file = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_STORE

    for rank, chunk in enumerate(retrieve(task, n, store_file), start=1):
        print(f"\n#{rank}  score={chunk['score']:.3f}  {chunk['id']}")
        print(f"    symbols: {', '.join(chunk['symbols'])}")


if __name__ == "__main__":
    main()

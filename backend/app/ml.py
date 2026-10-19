from typing import Protocol
import re
import numpy as np
from app.config import settings


def normalize(vector):
    vector = np.asarray(vector, dtype=np.float32)
    if vector.ndim != 1 or not np.isfinite(vector).all() or np.linalg.norm(vector) == 0:
        raise ValueError('Embedding must be a finite nonzero vector')
    return vector / np.linalg.norm(vector)


class VectorStore(Protocol):
    def serialize(self, vector: np.ndarray) -> bytes: ...
    def deserialize(self, data: bytes, dimension: int) -> np.ndarray: ...


class SQLiteVectors:
    def serialize(self, vector):
        return normalize(vector).astype('<f4').tobytes()

    def deserialize(self, data, dimension):
        vector = np.frombuffer(data, dtype='<f4').copy()
        if vector.size != dimension or not np.isfinite(vector).all():
            raise ValueError('Incompatible serialized vector')
        return normalize(vector)


class ModelRuntime:
    def __init__(self, config=settings):
        self.config = config
        self._bi = None
        self._cross = None
        self.version = f'{config.bi_encoder}@{config.bi_revision}'
        self.cross_version = f'{config.cross_encoder}@{config.cross_revision}:sigmoid'

    def load(self, download=False):
        import torch
        from sentence_transformers import SentenceTransformer, CrossEncoder
        torch.set_num_threads(2)
        if self._bi is None:
            self._bi = SentenceTransformer(self.config.bi_encoder, revision=self.config.bi_revision, device='cpu', local_files_only=not download)
        if self._cross is None:
            self._cross = CrossEncoder(self.config.cross_encoder, revision=self.config.cross_revision, device='cpu', activation_fn=torch.nn.Sigmoid(), local_files_only=not download)

    def embed(self, text):
        self.load()
        text = re.sub(r'\s+', ' ', text).strip()
        tokens = self._bi.tokenizer.encode(text, add_special_tokens=False)
        chunks = [tokens[i:i + 192] for i in range(0, len(tokens), 192)]
        texts = [self._bi.tokenizer.decode(chunk, skip_special_tokens=True) for chunk in chunks]
        embeddings = self._bi.encode(texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
        return normalize(np.average(embeddings, axis=0, weights=[len(c) for c in chunks]))

    def score(self, pairs):
        self.load()
        return np.asarray(self._cross.predict(pairs, show_progress_bar=False), dtype=float).reshape(-1)


def exact_nearest(vector, clusters, vectors):
    if not clusters:
        return None, -1.0
    matrix = np.stack([vectors.deserialize(c.centroid_embedding, c.embedding_dimension) for c in clusters])
    similarities = matrix @ normalize(vector)
    index = int(np.argmax(similarities))
    return clusters[index], float(similarities[index])

"""Local embedding service (Phase 4).

Produces REAL vector embeddings via the local Ollama runtime (model
``nomic-embed-text``, 768 dims) so memory retrieval is semantic — similar
meaning, not shared keywords. Cosine similarity is computed in pure Python (no
extra dependency); the corpus is small (company memories), so this is ample.

If the embedding backend is unavailable the service degrades gracefully
(``embed`` returns ``None``) and callers fall back to keyword recall — semantic
search is an enhancement, never a hard dependency.
"""

from __future__ import annotations

import math

from sqlalchemy import select
from sqlalchemy.orm import Session

EMBED_MODEL = "nomic-embed-text"


class EmbeddingService:
    def __init__(self, db: Session):
        self.db = db

    def _base_url(self) -> str | None:
        # Reuse the configured Ollama provider's base_url.
        from app.models.orchestration import AIProvider, ProviderConfig

        prov = self.db.scalar(select(AIProvider).where(AIProvider.name == "ollama"))
        if prov is None:
            return None
        cfg = self.db.scalar(
            select(ProviderConfig).where(
                ProviderConfig.provider_id == prov.id, ProviderConfig.key == "base_url"
            )
        )
        return (cfg.value if cfg and cfg.value else "http://host.docker.internal:11434").rstrip("/")

    def embed(self, text: str) -> list[float] | None:
        """Return a unit-normalised embedding for ``text``, or None on failure."""
        text = (text or "").strip()
        if not text:
            return None
        base = self._base_url()
        if not base:
            return None
        try:
            import httpx

            with httpx.Client(timeout=30.0) as client:
                r = client.post(
                    f"{base}/api/embed",
                    json={"model": EMBED_MODEL, "input": text[:4000]},
                )
                r.raise_for_status()
                data = r.json()
            vecs = data.get("embeddings")
            vec = vecs[0] if vecs and isinstance(vecs[0], list) else data.get("embedding")
            if not vec:
                return None
            norm = math.sqrt(sum(x * x for x in vec)) or 1.0
            return [x / norm for x in vec]
        except Exception:
            return None

    @staticmethod
    def cosine(a: list[float] | None, b: list[float] | None) -> float:
        """Cosine similarity of two (assumed unit-normalised) vectors."""
        if not a or not b or len(a) != len(b):
            return 0.0
        return sum(x * y for x, y in zip(a, b))

    def available(self) -> bool:
        return self.embed("healthcheck") is not None

import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from pathlib import Path

import streamlit as st
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_FALLBACK_MODELS, EMBEDDING_MODEL_NAME


EMBEDDING_LOAD_TIMEOUT_SECONDS = 30


class EmbeddingSetupError(RuntimeError):
    """Raised when the embedding model cannot be initialized."""


@dataclass
class EmbeddingStatus:
    cache_available: bool
    model_available: bool
    offline_mode: bool
    cache_path: str | None
    model_name: str | None
    message: str


class LocalSentenceTransformerEmbeddings(Embeddings):
    """Lightweight LangChain-compatible wrapper around SentenceTransformer."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name, local_files_only=True)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embedding.tolist()


def _get_hf_home() -> Path:
    return Path(
        os.environ.get("HF_HOME")
        or os.environ.get("HUGGINGFACE_HUB_CACHE")
        or Path.home() / ".cache" / "huggingface"
    )


def _repo_cache_dir(model_name: str) -> Path:
    repo_id = model_name.replace("/", "--")
    return _get_hf_home() / "hub" / f"models--{repo_id}"


def _find_cached_snapshot(model_name: str) -> tuple[bool, str | None]:
    snapshots_dir = _repo_cache_dir(model_name) / "snapshots"
    if not snapshots_dir.exists():
        return False, None

    for snapshot_dir in snapshots_dir.iterdir():
        if snapshot_dir.is_dir() and (snapshot_dir / "config.json").exists():
            return True, str(snapshot_dir)

    return False, None


def check_embedding_cache() -> tuple[bool, str | None]:
    status = check_embedding_model_available()
    return status.cache_available, status.cache_path


def check_embedding_model_available() -> EmbeddingStatus:
    for model_name in EMBEDDING_FALLBACK_MODELS:
        cache_available, cache_path = _find_cached_snapshot(model_name)
        if cache_available:
            message = (
                "Embedding model found locally."
                if model_name == EMBEDDING_MODEL_NAME
                else f"Primary embedding model missing. Using local fallback: {model_name}"
            )
            return EmbeddingStatus(
                cache_available=True,
                model_available=True,
                offline_mode=True,
                cache_path=cache_path,
                model_name=model_name,
                message=message,
            )

    fallback_list = "\n".join(f"- {model_name}" for model_name in EMBEDDING_FALLBACK_MODELS)
    return EmbeddingStatus(
        cache_available=False,
        model_available=False,
        offline_mode=True,
        cache_path=None,
        model_name=None,
        message=(
            "Embedding model not found locally.\n\n"
            "Download one of these models once, then restart the app:\n"
            f"{fallback_list}"
        ),
    )


def _build_embedding_model(model_name: str) -> LocalSentenceTransformerEmbeddings:
    return LocalSentenceTransformerEmbeddings(model_name)


def load_embedding_model() -> LocalSentenceTransformerEmbeddings:
    status = check_embedding_model_available()
    if not status.model_available or not status.model_name:
        raise EmbeddingSetupError(status.message)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_build_embedding_model, status.model_name)
        try:
            return future.result(timeout=EMBEDDING_LOAD_TIMEOUT_SECONDS)
        except FutureTimeoutError as exc:
            raise EmbeddingSetupError(
                "Embedding model loading timed out. Please verify the local model cache and try again."
            ) from exc
        except Exception as exc:
            raise EmbeddingSetupError(
                f"The embedding model '{status.model_name}' could not be loaded from the local cache."
            ) from exc


@st.cache_resource(show_spinner=False)
def get_embedding_model() -> LocalSentenceTransformerEmbeddings:
    return load_embedding_model()

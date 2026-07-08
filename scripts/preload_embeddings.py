from __future__ import annotations

from huggingface_hub import snapshot_download

from config import EMBEDDING_MODEL_NAME


def main() -> None:
    print(f"Downloading embedding model to local Hugging Face cache: {EMBEDDING_MODEL_NAME}")
    snapshot_download(repo_id=EMBEDDING_MODEL_NAME)
    print("Embedding model cache ready.")


if __name__ == "__main__":
    main()

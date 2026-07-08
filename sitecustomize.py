import os
import sys


def _looks_like_streamlit_process() -> bool:
    argv = " ".join(part.lower() for part in sys.argv[:3])
    return "streamlit" in argv


if _looks_like_streamlit_process():
    os.environ.setdefault("STREAMLIT_SERVER_FILE_WATCHER_TYPE", "none")

import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import os

import ollama
import streamlit as st

from config import DEFAULT_MODEL, FALLBACK_MODELS, LLM_NUM_CTX, LLM_NUM_PREDICT, LLM_NUM_THREAD


OLLAMA_CONNECT_TIMEOUT_SECONDS = 10
OLLAMA_DEBUG_LOGS = os.environ.get("OLLAMA_DEBUG_LOGS", "").strip().lower() in {"1", "true", "yes"}


class OllamaSetupError(RuntimeError):
    """Raised when the local Ollama setup is incomplete."""


def _debug_log(*parts) -> None:
    if OLLAMA_DEBUG_LOGS:
        print(*parts)


@dataclass
class OllamaStatus:
    installed: bool
    running: bool
    model_available: bool
    requested_model: str
    selected_model: str | None
    available_models: list[str]
    detection_status: str
    llm_ready: bool
    llm_test_message: str
    message: str


def check_ollama_installed() -> bool:
    return shutil.which("ollama") is not None


def _list_models():
    return ollama.list()


def check_ollama_running() -> bool:
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_list_models)
        try:
            future.result(timeout=OLLAMA_CONNECT_TIMEOUT_SECONDS)
            return True
        except Exception:
            return False


def _extract_model_names(response) -> list[str]:
    models = response.get("models", []) if isinstance(response, dict) else getattr(response, "models", [])
    names: list[str] = []
    for model in models:
        if isinstance(model, dict):
            name = model.get("model") or model.get("name")
        else:
            name = getattr(model, "model", None) or getattr(model, "name", None)
        if name:
            names.append(name)
    return names


def _normalize_model_name(model_name: str) -> str:
    return model_name.strip().lower().split(":")[0]


def _find_matching_model(model_name: str, available_models: list[str]) -> str | None:
    wanted = _normalize_model_name(model_name)
    for available_model in available_models:
        if _normalize_model_name(available_model) == wanted:
            return available_model
    return None


def _get_available_models() -> list[str]:
    return _extract_model_names(_list_models())


def check_model_exists(model_name: str) -> bool:
    try:
        return _find_matching_model(model_name, _get_available_models()) is not None
    except Exception:
        return False


def resolve_model_name(preferred_model: str = DEFAULT_MODEL) -> tuple[str | None, list[str]]:
    available_models = _get_available_models()
    for candidate in [preferred_model, *[m for m in FALLBACK_MODELS if m != preferred_model]]:
        match = _find_matching_model(candidate, available_models)
        if match:
            return match, available_models
    return None, available_models


def test_ollama_generation(model_name: str) -> tuple[bool, str]:
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": "Respond with the word OK"}],
            stream=False,
            options={
                "temperature": 0,
                "num_predict": 8,
                "num_ctx": 512,
            },
        )
        return True, response.get("message", {}).get("content", "").strip() or "OK"
    except Exception as exc:
        return False, str(exc)


def get_ollama_status(preferred_model: str = DEFAULT_MODEL) -> OllamaStatus:
    if not check_ollama_installed():
        return OllamaStatus(False, False, False, preferred_model, None, [], "Ollama executable not found.", False, "Ollama not installed", "Ollama is not installed. Download from https://ollama.com")

    if not check_ollama_running():
        return OllamaStatus(True, False, False, preferred_model, None, [], "Ollama service is not reachable.", False, "Ollama service not running", "Start Ollama using: ollama serve")

    try:
        selected_model, available_models = resolve_model_name(preferred_model)
    except Exception as exc:
        return OllamaStatus(True, True, False, preferred_model, None, [], f"Model detection failed: {exc}", False, "Model detection failed", f"Run: ollama pull {preferred_model}")

    _debug_log("Detected models:", available_models)
    _debug_log("Selected model:", selected_model)

    if not available_models:
        return OllamaStatus(True, True, False, preferred_model, None, [], "No local Ollama models detected.", False, "No models installed", f"No local Ollama models found.\n\nRun:\nollama pull {preferred_model}")

    if selected_model is None:
        return OllamaStatus(
            True,
            True,
            False,
            preferred_model,
            None,
            available_models,
            "Preferred and fallback models were not found.",
            False,
            "No supported model matched",
            "No supported Ollama model is available locally.\n\nRun one of:\n" + "\n".join(f"ollama pull {model_name}" for model_name in FALLBACK_MODELS),
        )

    llm_ready, llm_test_message = test_ollama_generation(selected_model)
    _debug_log("Model test passed:", llm_ready)

    return OllamaStatus(
        True,
        True,
        True,
        preferred_model,
        selected_model,
        available_models,
        f"Detected: {selected_model}",
        llm_ready,
        llm_test_message,
        "Model found." if llm_ready else f"LLM test failed: {llm_test_message}",
    )


@st.cache_data(ttl=30, show_spinner=False)
def get_llm_status() -> OllamaStatus:
    return get_ollama_status(DEFAULT_MODEL)


def _generate_response(model_name: str, prompt: str) -> str:
    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        options={
            "temperature": 0,
            "num_predict": LLM_NUM_PREDICT,
            "num_ctx": LLM_NUM_CTX,
            "num_thread": LLM_NUM_THREAD,
            "repeat_penalty": 1.05,
        },
    )
    return response.get("message", {}).get("content", "").strip()


def stream_response(model_name: str, prompt: str, timeout_seconds: int = 30):
    started_at = time.perf_counter()
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_generate_response, model_name, prompt)
        try:
            text = future.result(timeout=timeout_seconds)
        except Exception as exc:
            future.cancel()
            raise OllamaSetupError("LLM response taking too long.") from exc

    if not text:
        text = "I could not find this information in the uploaded PDF."

    for token in text.split():
        yield token + " "

    _debug_log("Ollama total response time:", round(time.perf_counter() - started_at, 2))

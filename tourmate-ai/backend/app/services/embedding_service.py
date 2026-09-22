"""
Embedding Service abstraction for semantic representation.
Produces normalized 384-dimensional vectors matching all-MiniLM-L6-v2.
Thread-safe, lazy loading with bounded resource consumption and graceful fallback.
"""
import os
import sys
import hashlib
import logging
import threading
import asyncio
import urllib.request
from typing import List
import numpy as np

logger = logging.getLogger(__name__)

_tokenizer = None
_session = None
_load_failed = False
_model_lock = threading.Lock()

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "all-MiniLM-L6-v2.onnx")
TOKENIZER_PATH = os.path.join(MODEL_DIR, "tokenizer.json")

MODEL_URL = "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/onnx/model.onnx"
TOKENIZER_URL = "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/raw/main/tokenizer.json"


def _download_file(url: str, dest_path: str, timeout: int = 45):
    """Atomically downloads a file using a .tmp file to prevent corruption."""
    tmp_path = dest_path + ".tmp"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TourMate-ModelDownloader/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response, open(tmp_path, "wb") as out_file:
            chunk_size = 1024 * 1024  # 1MB
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
        # Atomic rename
        os.replace(tmp_path, dest_path)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


def ensure_model_downloaded(timeout: int = 45) -> bool:
    """Pre-downloads model files if not present on disk. Safe to run during buildCommand."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    success = True
    if not os.path.exists(TOKENIZER_PATH):
        try:
            logger.info("Downloading embedding tokenizer to %s", TOKENIZER_PATH)
            _download_file(TOKENIZER_URL, TOKENIZER_PATH, timeout=timeout)
        except Exception as exc:
            logger.warning("Tokenizer download failed: %s", exc)
            success = False

    if not os.path.exists(MODEL_PATH):
        try:
            logger.info("Downloading ONNX model to %s", MODEL_PATH)
            _download_file(MODEL_URL, MODEL_PATH, timeout=timeout)
        except Exception as exc:
            logger.warning("ONNX model download failed: %s", exc)
            success = False

    return success


def _fallback_embedding(text_val: str) -> List[float]:
    """
    Deterministic pseudo-semantic fallback embedding (384-d normalized).
    Used when ONNX model fails to load or during memory constraints.
    Guarantees the application never crashes or hangs on semantic operations.
    """
    # Hash tokens and populate 384 dimensions deterministically
    vec = np.zeros(384, dtype=np.float32)
    words = text_val.lower().split()
    if not words:
        words = [text_val.lower()]
    for i, word in enumerate(words):
        h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
        for d in range(6):
            idx = (h + d * 64) % 384
            vec[idx] += 1.0 / (i + 1)

    norm = np.linalg.norm(vec)
    if norm > 1e-9:
        vec = vec / norm
    else:
        vec[0] = 1.0
    return [round(float(x), 6) for x in vec]


def _ensure_model_loaded():
    global _tokenizer, _session, _load_failed
    if _session is not None and _tokenizer is not None:
        return
    if _load_failed:
        return

    with _model_lock:
        if _session is not None and _tokenizer is not None:
            return
        if _load_failed:
            return

        try:
            import onnxruntime as ort
            from tokenizers import Tokenizer

            ensure_model_downloaded(timeout=20)

            if not os.path.exists(TOKENIZER_PATH) or not os.path.exists(MODEL_PATH):
                logger.warning("Model files not found on disk. Falling back to deterministic embeddings.")
                _load_failed = True
                return

            _tokenizer = Tokenizer.from_file(TOKENIZER_PATH)

            # Limit thread count to 1 to prevent CPU starvation and memory spikes on Render free tier
            sess_options = ort.SessionOptions()
            sess_options.intra_op_num_threads = 1
            sess_options.inter_op_num_threads = 1
            sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC

            _session = ort.InferenceSession(MODEL_PATH, sess_options=sess_options)
            logger.info("Embedding ONNX model and tokenizer loaded successfully.")
        except Exception as exc:
            logger.warning("Failed to initialize ONNX embedding model (%s). Using fallback: %s", type(exc).__name__, exc)
            _load_failed = True


def get_embedding(text: str) -> List[float]:
    """
    Generate normalized 384-dimensional vector embedding for given text.
    Production-safe: falls back gracefully if model loading fails.
    """
    if not text or not text.strip():
        return [0.0] * 384

    try:
        _ensure_model_loaded()

        if _session is None or _tokenizer is None:
            return _fallback_embedding(text)

        encoding = _tokenizer.encode(text)
        input_ids = np.array([encoding.ids], dtype=np.int64)
        attention_mask = np.array([encoding.attention_mask], dtype=np.int64)
        token_type_ids = np.array([encoding.type_ids], dtype=np.int64)

        outputs = _session.run(
            None,
            {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "token_type_ids": token_type_ids,
            },
        )
        token_embeddings = outputs[0]
        input_mask_expanded = np.expand_dims(attention_mask, -1).astype(float)
        sum_embeddings = np.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = np.clip(input_mask_expanded.sum(1), a_min=1e-9, a_max=None)
        pooled = sum_embeddings / sum_mask

        # L2 normalize
        norm = np.linalg.norm(pooled, ord=2, axis=1, keepdims=True)
        normalized = pooled / np.clip(norm, a_min=1e-12, a_max=None)
        return [round(float(x), 6) for x in normalized[0]]
    except Exception as exc:
        logger.warning("Error computing ONNX embedding (%s). Using fallback: %s", type(exc).__name__, exc)
        return _fallback_embedding(text)


async def async_get_embedding(text: str) -> List[float]:
    """Async wrapper that runs embedding generation in a thread pool without blocking event loop."""
    return await asyncio.to_thread(get_embedding, text)


if __name__ == "__main__":
    if "--download-only" in sys.argv:
        print("Ensuring embedding models are pre-downloaded...")
        ok = ensure_model_downloaded()
        print("Download result:", ok)

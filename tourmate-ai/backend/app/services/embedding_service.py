"""
Embedding Service abstraction for semantic representation.
Produces normalized 384-dimensional vectors matching all-MiniLM-L6-v2.
"""
import os
import urllib.request
from typing import List
import numpy as np

_tokenizer = None
_session = None

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "all-MiniLM-L6-v2.onnx")
TOKENIZER_PATH = os.path.join(MODEL_DIR, "tokenizer.json")

MODEL_URL = "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/onnx/model.onnx"
TOKENIZER_URL = "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/raw/main/tokenizer.json"


def _ensure_model_loaded():
    global _tokenizer, _session
    if _session is not None and _tokenizer is not None:
        return

    import onnxruntime as ort
    from tokenizers import Tokenizer

    os.makedirs(MODEL_DIR, exist_ok=True)
    if not os.path.exists(TOKENIZER_PATH):
        urllib.request.urlretrieve(TOKENIZER_URL, TOKENIZER_PATH)
    if not os.path.exists(MODEL_PATH):
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

    _tokenizer = Tokenizer.from_file(TOKENIZER_PATH)
    _session = ort.InferenceSession(MODEL_PATH)


def get_embedding(text: str) -> List[float]:
    """
    Generate normalized 384-dimensional vector embedding for given text using all-MiniLM-L6-v2.
    """
    if not text or not text.strip():
        return [0.0] * 384

    _ensure_model_loaded()

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

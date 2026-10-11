import os
import urllib.request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "piper")

MODELS = {
    "hi_IN-pratham-medium": {
        "onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/pratham/medium/hi_IN-pratham-medium.onnx",
        "json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/pratham/medium/hi_IN-pratham-medium.onnx.json"
    }
}

def download_models():
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    for model_name, files in MODELS.items():
        for file_type, url in files.items():
            filename = f"{model_name}.{file_type}"
            filepath = os.path.join(MODELS_DIR, filename)
            
            if not os.path.exists(filepath):
                logger.info(f"Downloading {filename}...")
                try:
                    urllib.request.urlretrieve(url, filepath)
                    logger.info(f"Successfully downloaded {filename}")
                except Exception as e:
                    logger.error(f"Failed to download {filename}: {e}")
            else:
                logger.info(f"{filename} already exists.")

if __name__ == "__main__":
    download_models()

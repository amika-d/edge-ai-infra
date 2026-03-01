"""
scripts/download_model.py

Downloads a HuggingFace model into ./models/<org>/<model-name>
This is the path vLLM expects when you mount ./models into the container.

Usage:
    uv run scripts/download_model.py
    uv run scripts/download_model.py --model Qwen/Qwen2.5-7B-Instruct-AWQ
"""
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import snapshot_download, HfApi



load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_MODEL = os.getenv("MODEL_ID", "Qwen/Qwen2.5-7B-Instruct-AWQ")
MODELS_DIR    = Path(__file__).parent.parent / "models"  # project_root/models/

# ── Helpers ───────────────────────────────────────────────────────────────────

def check_token(token: str | None) -> str | None:
    if not token or token == "hf_your_token_here":
        print("⚠️  HF_TOKEN not set — only public ungated models will work")
        print("   Set HF_TOKEN in .env and accept the model license on huggingface.co\n")
        return None
    return token


def check_disk_space(path: Path, min_gb: int = 10):
    import shutil
    free = shutil.disk_usage(path).free / (1024 ** 3)
    if free < min_gb:
        print(f"⚠️  Low disk space: {free:.1f}GB free — model may need {min_gb}GB+")
    else:
        print(f"💾 Disk space available: {free:.1f}GB")


def get_save_path(model_id: str) -> Path:
    """
    Qwen/Qwen2.5-7B-Instruct-AWQ → models/Qwen/Qwen2.5-7B-Instruct-AWQ
    """
    return MODELS_DIR / model_id


# ── Main ──────────────────────────────────────────────────────────────────────

def download_model(model_id: str):
    token     = check_token(os.getenv("HF_TOKEN"))
    save_path = get_save_path(model_id)

    save_path.mkdir(parents=True, exist_ok=True)
    check_disk_space(MODELS_DIR)

    print(f"\n📥 Model  : {model_id}")
    print(f"📁 Saving : {save_path}")
    print(f"⏳ Starting download...\n")

    try:
        snapshot_download(
            repo_id=model_id,
            local_dir=str(save_path),
            token=token,
            ignore_patterns=[
                "*.pt",           # skip pytorch bins — vLLM uses safetensors
                "*.bin",          # skip old format
                "original/*",     # skip original weights folder
                "*.gguf",         # skip GGUF format
            ],
        )
    except Exception as e:
        if "401" in str(e) or "403" in str(e):
            print(f"\n❌ Auth error — {e}")
            print(f"   1. Accept the model license at: huggingface.co/{model_id}")
            print(f"   2. Make sure HF_TOKEN is set in .env with read access")
            sys.exit(1)
        raise

    print(f"\n✅ Done — model saved to {save_path}")
    print(f"\n📋 Files downloaded:")
    for f in sorted(save_path.rglob("*")):
        if f.is_file():
            size_mb = f.stat().st_size / (1024 ** 2)
            print(f"   {f.relative_to(save_path)}  ({size_mb:.0f}MB)")

    print(f"\n🚀 Start the stack with:")
    print(f"   docker compose up -d")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download a HuggingFace model for vLLM.")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"HuggingFace model ID (default: {DEFAULT_MODEL})",
    )
    args = parser.parse_args()

    download_model(args.model)
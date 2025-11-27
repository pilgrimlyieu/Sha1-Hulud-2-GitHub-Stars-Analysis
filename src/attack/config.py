import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def load_config(path: str | None = None) -> dict:
    """Load configuration from JSON file and overlay environment variables."""
    if path is None:
        path = Path(__file__).parents[2] / "config.json"
    else:
        path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # Overlay environment values
    cfg["github_token"] = os.getenv(cfg.get("github_token_env", "GITHUB_TOKEN"))
    cfg["encryption_key"] = os.getenv(cfg.get("encryption_key_env", "ENCRYPTION_KEY"))

    return cfg

import json
import os

from dotenv import load_dotenv

load_dotenv()


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def get_categories() -> list[str]:
    """Allowed product categories, written by scripts/prepare_data.py."""
    path = env("CATEGORIES_PATH", "data/categories.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

import os

from dotenv import load_dotenv

load_dotenv()

def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set. Add it to your .env file.")
    return value

BASE_URL = _require("BASE_URL")
API_KEY = _require("API_KEY")
MODEL = os.environ.get("MODEL", "deepseek/deepseek-v4-flash")

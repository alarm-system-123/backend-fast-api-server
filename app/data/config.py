"""Configuration module to load environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Config: # pylint: disable=too-few-public-methods
    """Configuration class to hold environment variables."""
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    MONGO_URL = os.getenv("MONGO_URL")

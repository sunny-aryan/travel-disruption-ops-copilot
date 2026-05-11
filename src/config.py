import os

from dotenv import load_dotenv


load_dotenv()


def get_openai_api_key() -> str | None:
    """Return OpenAI API key from local environment, if configured."""
    return os.getenv("OPENAI_API_KEY")


def is_openai_configured() -> bool:
    """Return whether OpenAI API access is configured locally."""
    return bool(get_openai_api_key())
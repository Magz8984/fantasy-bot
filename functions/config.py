import os
from dataclasses import dataclass
from pathlib import Path

# Load environment variables from a .env file if it exists


def load_env(path: str = ".env"):
    env_file = Path(path)

    if not env_file.exists():
        return

    for line in env_file.read_text().splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)

        os.environ.setdefault(
            key.strip(),
            value.strip().strip('"').strip("'")
        )


@dataclass(frozen=True)
class Config:
    environment: str
    port: int
    # database_url: str
    claude_api_key: str
    host: str


def get_config() -> Config:
    load_env()

    # database_url = os.getenv("DATABASE_URL")

    # if not database_url:
    #     raise RuntimeError("DATABASE_URL is required")

    return Config(
        environment=os.getenv("ENVIRONMENT", "development"),
        port=int(os.getenv("PORT_NUMBER", "8000")),
        # database_url=os.getenv("DATABASE_URL"),
        claude_api_key=os.getenv("CLAUDE_API_KEY"),
        host=os.getenv("HOST")
    )

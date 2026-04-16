from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import os


@dataclass
class Config:
    TOKEN: str
    DATABASE_URL: str
    REMINDER_1_DAY: int


def load_config() -> Config:
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
    
    return Config(
        TOKEN=os.getenv("TOKEN"),
        DATABASE_URL=os.getenv("DATABASE_URL"),
        REMINDER_1_DAY=int(os.getenv("REMINDER_1_DAY")),
    )


config = load_config()
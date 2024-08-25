from json import loads, dump
import sys
import pathlib
import logging
import os
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, validator, ValidationError

CONFIG_FILE = pathlib.Path(os.path.dirname(__file__), "config.json")


# Logging
def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s:[%(funcName)s] %(message)s"
    )
    logging.basicConfig(format="%(asctime)s %(levelname)-8s:[%(funcName)s] %(message)s")
    logging.getLogger("kafka").setLevel(logging.CRITICAL)


class Camera(BaseModel):
    name: str
    url: str
    audio: bool = False  # Default to False if not provided


class Kafka(BaseModel):
    api_url: str
    audio_topic: str
    images_topic: str


class Config(BaseModel):
    cameras: List[Camera]
    cameras_dir: str
    kafka: Optional[Kafka] = None
    audio_duration: Optional[int] = None
    still_images: Optional[str] = None
    still_image_interval: Optional[int] = None


def genconf() -> Optional[Config]:
    try:
        configuration = Config.parse_file(CONFIG_FILE)
        return configuration
    except ValidationError as e:
        logging.error(
            f"{CONFIG_FILE} is not a valid Config file, Errors: \n {e.json(indent=4)}"
        )
        sys.exit(1)
    except FileNotFoundError as e:
        logging.error(f"Config File: '{CONFIG_FILE}' could not be found")
        sys.exit(1)

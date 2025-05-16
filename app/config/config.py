from pathlib import Path
import yaml
from typing import Dict, Any
import logging


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        self.config_data = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = Path(__file__).parent / "config.yaml"
            with open(config_path, "r") as file:
                return yaml.safe_load(file)
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
            raise RuntimeError("Failed to load configuration")

    @property
    def system_prompt(self) -> str:
        return self.config_data.get("system_prompt", "")

    @property
    def model_name(self) -> str:
        return self.config_data.get("model", "gpt-4o-mini")

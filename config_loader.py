# qlik_monitor/config_loader.py
import os
import yaml
from dotenv import load_dotenv
from typing import Optional


class ConfigLoader:
    def __init__(self):
        """
        Load environment variables from .env file if provided.
        """
        load_dotenv(dotenv_path=".env")

    @staticmethod
    def load_yaml(path: str) -> dict:
        """
        Load configuration from YAML file.
        """
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def load(self, yaml_path: str, enrich_with_env: bool = True) -> dict:
        """
        Load YAML config and optionally enrich it with environment variables.
        """
        config = self.load_yaml(yaml_path)

        if enrich_with_env:
            # Update Qlik Sense section
            qlik_sense_env = {
                "server": os.getenv("QLIK_SENSE_SERVER"),
                "user_directory": os.getenv("QLIK_SENSE_USER_DIRECTORY"),
                "user_id": os.getenv("QLIK_SENSE_USER_ID"),
                "password": os.getenv("QLIK_SENSE_PASSWORD")
            }

            config.setdefault("qlik_sense", {})
            for key, value in qlik_sense_env.items():
                if value is not None:
                    config["qlik_sense"][key] = value



            # Update Email section
            email_env = {
                "sender_username": os.getenv("EMAIL_SENDER_USERNAME"),
                "sender_password": os.getenv("EMAIL_SENDER_PASSWORD")
            }

            config.setdefault("email", {})
            for key, value in email_env.items():
                if value is not None:
                    config["email"][key] = value

        return config

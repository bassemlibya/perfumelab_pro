# config/app_config.py
import os
import json

class AppConfig:
    APP_NAME = "PerfumeLab Pro"
    APP_VERSION = "2.0.0"
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Database
    DB_PATH = os.path.join(APP_DIR, "perfumelab.db")
    SCHEMA_PATH = os.path.join(APP_DIR, "src", "core", "database", "migrations", "001_initial_schema.sql")

    # Resources
    RESOURCES_DIR = os.path.join(APP_DIR, "src", "resources")
    FONTS_DIR = os.path.join(RESOURCES_DIR, "fonts")
    IMAGES_DIR = os.path.join(RESOURCES_DIR, "images")
    I18N_DIR = os.path.join(RESOURCES_DIR, "i18n")

    # Themes
    THEMES = ['light', 'dark', 'modern']
    DEFAULT_THEME = 'light'

    # POS
    POS_DEFAULT_CURRENCY = 'USD'
    POS_ALLOW_NEGATIVE_STOCK = False
    POS_MAX_DISCOUNT_PERCENT = 50
    POS_RECEIPT_WIDTH = 80  # mm

    # Security
    SESSION_TIMEOUT = 30  # minutes
    MAX_LOGIN_ATTEMPTS = 5
    PASSWORD_MIN_LENGTH = 6

    @classmethod
    def load_currencies_config(cls):
        config_path = os.path.join(cls.APP_DIR, "config", "currencies.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

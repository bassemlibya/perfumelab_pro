# core/database/connection.py
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

class DatabaseManager:
    _instance = None
    _db_path = None

    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._db_path = db_path or "perfumelab.db"
        return cls._instance

    def __init__(self, db_path: str = None):
        if db_path:
            self._db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    def execute(self, query: str, params: tuple = ()) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        results = self.execute(query, params)
        return results[0] if results else None

    def execute_insert(self, query: str, params: tuple = ()) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def execute_update(self, query: str, params: tuple = ()) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def initialize_database(self, schema_path: str = None):
        if schema_path is None:
            # المسار النسبي الصحيح من مكان ملف connection.py
            current_file = os.path.abspath(__file__)
            schema_path = os.path.join(os.path.dirname(current_file), 'migrations', '001_initial_schema.sql')

        if not os.path.exists(self._db_path):
            if not os.path.exists(schema_path):
                raise FileNotFoundError("Schema file not found: %s" % schema_path)

            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()

            with self.get_connection() as conn:
                conn.executescript(schema)
                conn.commit()
            print("Database created: %s" % self._db_path)
        else:
            print("Database exists: %s" % self._db_path)

    def backup(self, backup_path: str = None):
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = "backup_%s.db" % timestamp
        with self.get_connection() as source:
            with sqlite3.connect(backup_path) as dest:
                source.backup(dest)
        return backup_path

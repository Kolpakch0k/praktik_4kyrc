import os
from contextlib import contextmanager
from dotenv import load_dotenv
import mysql.connector

load_dotenv()


class Database:
    def __init__(self):
        self.config = {
            "host": os.getenv("DB_HOST", "127.0.0.1"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", "medical_appointments"),
            "autocommit": True,
            "charset": "utf8mb4",
        }
        self.connection = self.connect()

    def connect(self):
        return mysql.connector.connect(**self.config)

    def execute(self, sql, params=()):
        try:
            with self.connection.cursor() as c:
                c.execute(sql, params)
            self.connection.commit()
        except mysql.connector.Error:
            self.connection.rollback()
            raise

    def rows(self, sql, params=()):
        with self.connection.cursor() as c:
            c.execute(sql, params)
            return c.fetchall()

    def one(self, sql, params=()):
        with self.connection.cursor() as c:
            c.execute(sql, params)
            return c.fetchone()

    @contextmanager
    def transaction(self):
        self.connection.start_transaction()
        try:
            with self.connection.cursor() as c:
                yield c
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def dashboard(self):
        return (
            self.one("SELECT COUNT(*) FROM patients")[0],
            self.one("SELECT COUNT(*) FROM doctors")[0],
            self.one("SELECT COUNT(*) FROM appointments")[0],
            self.one(
                "SELECT COUNT(*) FROM appointments WHERE appointment_date=CURDATE() AND status='активна'"
            )[0],
        )

    def close(self):
        if self.connection.is_connected():
            self.connection.close()

import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key"
    DB_USER = os.environ.get("DB_USER") or "postgres_user"
    DB_PASSWORD = os.environ.get("DB_PASSWORD") or "postgres_password"
    DB_HOST = os.environ.get("DB_HOST") or "localhost"
    DB_PORT = os.environ.get("DB_PORT") or "5432"
    DB_NAME = os.environ.get("DB_NAME") or "data_analytics_db"

    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = "uploads"
    ALLOWED_EXTENSIONS = {"csv", "xlsx"}
    MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


class TestConfig:
    TESTING = True
    DB_USER = os.environ.get("DB_USER") or "postgres_user"
    DB_PASSWORD = os.environ.get("DB_PASSWORD") or "postgres_password"
    DB_HOST = os.environ.get("DB_HOST") or "localhost"
    DB_PORT = os.environ.get("DB_PORT") or "5432"
    DB_NAME = os.environ.get("TEST_DB_NAME") or "test_db"

    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "tests", "test_uploads")
    CELERY_BROKER_URL = "memory://"
    CELERY_RESULT_BACKEND = "cache+memory://"
    ALLOWED_EXTENSIONS = {"csv", "xlsx"}

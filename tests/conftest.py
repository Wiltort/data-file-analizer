import pytest
from io import BytesIO
import os
import sys
from sqlalchemy_utils import create_database, database_exists

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import db as _db
from config import TestConfig
import pandas as pd


@pytest.fixture(scope="module")
def app():
    """Фикстура приложения"""
    if not os.path.exists(TestConfig.UPLOAD_FOLDER):
        os.makedirs(TestConfig.UPLOAD_FOLDER, exist_ok=True)
    app = create_app(TestConfig)
    if not database_exists(app.config["SQLALCHEMY_DATABASE_URI"]):
        create_database(app.config["SQLALCHEMY_DATABASE_URI"])
    with app.app_context():
        _db.create_all()
    yield app
    with app.app_context():
        _db.drop_all()
    # Очистка тестовых файлов
    for f in os.listdir(TestConfig.UPLOAD_FOLDER):
        os.remove(os.path.join(TestConfig.UPLOAD_FOLDER, f))


@pytest.fixture(scope="module")
def client(app):
    """Тестовый клиент"""
    return app.test_client()


@pytest.fixture(scope="module")
def db(app):
    """Фикстура базы данных"""
    return _db


@pytest.fixture
def sample_csv():
    """Генерация тестового CSV"""
    data = BytesIO()
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "value": [10.5, 20.3, 15.7, None],
            "text_column": ["jr", "sss", "ssw2", "346374"],
        }
    )
    df.to_csv(data, index=False)
    data.seek(0)
    return data


@pytest.fixture
def sample_excel():
    """Генерация тестового Excel"""
    data = BytesIO()
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "value": [10.5, 20.3, 15.7, None],
            "text_column": ["jr", "sss", "ssw2", "346374"],
        }
    )
    with pd.ExcelWriter(data, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    data.seek(0)
    return data

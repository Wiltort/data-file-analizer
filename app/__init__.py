from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

# Инициализация расширений
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    """Фабрика приложений Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Инициализация расширений с приложением
    db.init_app(app)
    migrate.init_app(app, db)

    # Регистрация blueprints
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    @app.route('/test')
    def test_page():
        return 'Приложение работает!'

    return app

from app import models  # Импорт моделей для работы с миграциями
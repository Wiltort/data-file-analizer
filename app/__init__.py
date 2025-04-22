from flask import Flask
from sqlalchemy_utils.functions import database_exists, create_database
from .extensions import db, migrate, Base

def create_app(config_class='config.Config'):
    """Фабрика приложений Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Инициализация расширений с приложением
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        if not database_exists(db.engine.url):
            create_database(db.engine.url)
            Base.metadata.create_all(db.engine)

    # Регистрация blueprints
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    @app.route('/test')
    def test_page():
        return 'Приложение работает!'

    return app
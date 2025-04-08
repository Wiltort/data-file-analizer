import os
from app import create_app
from config import Config


app = create_app(Config)

if __name__ == '__main__':
    # Создаем папку для загрузок, если ее нет
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Запускаем приложение
    app.run(host=app.config.get('HOST', '0.0.0.0'), 
            port=app.config.get('PORT', 5000),
            debug=app.config.get('DEBUG', True))

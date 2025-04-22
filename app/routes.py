import os
from flask import Blueprint, jsonify, request, current_app
from .extensions import db
from .models import DataFile, DataAnalysis, AnalysisTask
from werkzeug.utils import secure_filename
from datetime import datetime

bp = Blueprint('api', __name__, url_prefix='/api/v1')


def allowed_file(filename: str) -> bool:
    extensions = current_app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def save_file(file):
    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return filename, filepath

@bp.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'HELLO'})


@bp.route('/upload', methods=['POST'])
def upload_file():
    """Loads data file (CSV/Excel)"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(filename=file.filename):
        return jsonify({'error': 'Invalid file type'}), 415
    
    try:
        filename, filepath = save_file(file)
        
        # Сохраняем метаданные в БД
        new_file = DataFile(
            filename=filename,
            file_type=filename.rsplit('.', 1)[1].lower(),
            file_size=os.path.getsize(filepath),
            original_filename=file.filename,
            upload_date=datetime.now()
        )
        db.session.add(new_file)
        db.session.commit()
        return jsonify({
            'id': new_file.id,
            'filename': new_file.filename,
            'message': 'File uploaded successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
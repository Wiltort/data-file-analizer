import os
import pandas as pd
from flask import Blueprint, jsonify, request, current_app
from .extensions import db
from .models import DataFile, DataAnalysis, AnalysisTask
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.utils.data_processor import reading_methods, analyze_data, allowed_file, save_file

bp = Blueprint("api", __name__, url_prefix="/api/v1")


@bp.route("/upload", methods=["POST"])
def upload_file():
    """Loads data file (CSV/Excel)"""
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(filename=file.filename):
        return jsonify({"error": "Invalid file type"}), 415

    try:
        filename, filepath = save_file(file)
        # Сохраняем метаданные в БД
        new_file = DataFile(
            filename=filename,
            file_type=filename.rsplit(".", 1)[1].lower(),
            file_size=os.path.getsize(filepath),
            original_filename=file.filename,
            upload_date=datetime.now(),
        )
        db.session.add(new_file)
        db.session.commit()
        return (
            jsonify(
                {
                    "id": new_file.id,
                    "filename": new_file.filename,
                    "message": "File uploaded successfully",
                }
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/data/<int:file_id>/stats", methods=["GET"])
def get_stats(file_id):
    """Gets data summary"""
    try:
        data_file = db.session.get(DataFile, file_id)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], data_file.filename)
        # Проверка на наличие заголовков в таблице 
        first_row = reading_methods.get(data_file.file_type)(filepath, nrows=1)
        if all(isinstance(x, str) for x in first_row.values[0]):
            header=0
        else:
            header=None
        df = reading_methods.get(data_file.file_type)(filepath, header=header)
        if header is None:
            df.columns = [f'Column {col}' for col in df.columns]
        # Проверка наличия числовых колонок
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        return data_file.filename

    except Exception as e:
        return jsonify({"error": str(e)}), 500

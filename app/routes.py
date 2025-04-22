import os
import pandas as pd
from flask import Blueprint, jsonify, request, current_app
from .extensions import db
from .models import DataFile, DataAnalysis, AnalysisTask
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

bp = Blueprint("api", __name__, url_prefix="/api/v1")


reading_methods = {
    'csv': pd.read_csv,
    'xlsx': pd.read_excel
}

def allowed_file(filename: str) -> bool:
    extensions = current_app.config["ALLOWED_EXTENSIONS"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in extensions


def save_file(file):
    filename = secure_filename(file.filename)
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename

    while os.path.exists(os.path.join(upload_dir, new_filename)):
        new_filename = f"{base} ({counter}){ext}"
        counter += 1

    filepath = os.path.join(upload_dir, new_filename)
    file.save(filepath)
    return new_filename, filepath


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
        df = reading_methods.get(data_file.file_type)(filepath)
        # TODO Здесь дописать
        return data_file.filename

    except Exception as e:
        return jsonify({"error": str(e)}), 500

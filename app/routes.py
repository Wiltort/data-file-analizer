import os
from flask import Blueprint, jsonify, request
from .extensions import db
from .models import DataFile
from datetime import datetime
from app.utils.data_processor import allowed_file, save_file, analyze_data, clean_data

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
        print(e)
        return jsonify({"error": str(e)}), 500


@bp.route("/data/<int:file_id>/stats", methods=["GET"])
def get_stats(file_id):
    """Gets data summary"""
    db.get_or_404(DataFile, file_id)
    try:
        stats = analyze_data(file_id=file_id)
        return jsonify(stats)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/data/<int:file_id>/clean", methods=['POST'])
def get_cleaned_data(file_id):
    """Creates new file with cleaned data and gets cleaning report"""
    db.get_or_404(DataFile, file_id)
    handle_duplicates = request.args.get('handle_duplicates', 'drop')
    fill_missing = request.args.get('fill_missing', 'mean')
    force = bool(request.args.get('force', None))
    try:
        resp = clean_data(
            file_id=file_id,
            handle_duplicates=handle_duplicates,
            fill_missing=fill_missing,
            force=force
        )
        return jsonify(resp), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500

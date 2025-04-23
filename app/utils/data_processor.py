import pandas as pd
from flask import current_app
from sqlalchemy import select
from werkzeug.utils import secure_filename
import os
from app.extensions import db
from app.models import DataFile, DataAnalysis


reading_methods = {"csv": pd.read_csv, "xlsx": pd.read_excel}


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


def analyze_data(file_id: int):
    analysis_type = "basic_stats"
    stmt = select(DataAnalysis).where(
        DataAnalysis.data_file_id == file_id,
        DataAnalysis.analysis_type == analysis_type,
    )
    data_analysis = db.session.scalar(stmt)
    if data_analysis:
        return data_analysis.get_stats()
    try:
        data_file = db.session.get(DataFile, file_id)
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], data_file.filename)
        # Проверка на наличие заголовков в таблице
        first_row = reading_methods.get(data_file.file_type)(
            filepath, header=None, nrows=1
        )
        if all(isinstance(x, str) for x in first_row.values[0]):
            header = 0
        else:
            header = None
        df = reading_methods.get(data_file.file_type)(filepath, header=header)
        if header is None:
            df.columns = [f"Column {col}" for col in df.columns]

    except Exception as e:
        raise RuntimeError(e)

    stats = {
        "mean": df.mean(numeric_only=True).to_dict(),
        "median": df.median(numeric_only=True).to_dict(),
        "correlation": df.corr(numeric_only=True).to_dict(),
        "std": df.std(numeric_only=True).to_dict(),
        "min": df.min(numeric_only=True).to_dict(),
        "max": df.max(numeric_only=True).to_dict(),
    }
    analysis = DataAnalysis(
        data_file_id=file_id,
        analysis_type="basic_stats",
        stats_mean=stats["mean"],
        stats_median=stats["median"],
        stats_correlation=stats["correlation"],
        stats_std=stats["std"],
        stats_min=stats["min"],
        stats_max=stats["max"],
    )
    db.session.add(analysis)
    db.session.commit()
    return stats

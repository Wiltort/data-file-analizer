from datetime import datetime
from typing import Any, Dict
import pandas as pd
from flask import current_app
from sqlalchemy import select
from werkzeug.utils import secure_filename
import os
from app.extensions import db
from app.models import DataFile, DataAnalysis
from werkzeug.datastructures import FileStorage
from io import BytesIO
import tempfile


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
        return data_analysis.get_data()
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


def clean_data(
    file_id: int,
    handle_duplicates: str = "drop",  # ['drop', 'keep']
    fill_missing: str | None = None,
    force: bool = False,
) -> Dict[str, Any]:
    analysis_type = "cleaning"
    if not force:
        stmt = select(DataAnalysis).where(
            DataAnalysis.data_file_id == file_id,
            DataAnalysis.analysis_type == analysis_type,
        )
        data_cleaned = db.session.scalar(stmt)
        if data_cleaned:
            return data_cleaned.get_data()
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

    original_shape = df.shape
    data = {
        'duplicates_removed': 0,
        'missing_values_filled': 0,
        'cleaning_report': {
            'original_shape': original_shape,
            'actions_performed': []
        }
    }

    # 1. Обработка дупликатов
    if handle_duplicates == 'drop':
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            df = df.drop_duplicates()
            data["duplicates_removed"] = duplicates
        data['cleaning_report']["actions_performed"].append("duplicates_dropped")
    elif handle_duplicates != 'keep':
        raise ValueError(
            "Invalid value for handle_duplicates. Valid: 'drop' or 'keep'"
        )
    
    # 2. Заполнение пропущенных значений
    missing_before = df.isnull().sum().to_dict()
    if fill_missing == 'mean':
        fill_values = df.mean()
    elif fill_missing == 'median':
        fill_values = df.median()
    elif fill_missing == 'zero':
        fill_values = 0
    else:
        raise ValueError("Invalid fill_missing. Valid: 'mean', 'median', 'zero'")
    df = df.fillna(fill_values)
    missing_after = df.isnull().sum().to_dict()
    data['missing_values_filled'] = {
        'before': missing_before,
        'after': missing_after,
        'method': fill_missing
    }
    report['actions_performed'].append('missing_values_filled')

    # 3. Сохранение очищенных данных
    cleaned_filename = f"cleaned_{data_file.filename}"
    file_extension = data_file.file_type
    buffer = BytesIO()
    if file_extension == "csv":
        df.to_csv(buffer, index=False, encoding='utf-8')
        content_type = 'text/csv'
    elif file_extension == "xlsx":
        with tempfile.NamedTemporaryFile(suffix='.xlsx') as tmp:
            df.to_excel(tmp.name, index=False, engine='openpyxl')
            buffer.write(tmp.read())
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    buffer.seek(0)
    cleaned_file = FileStorage(
        stream=buffer,
        filename=cleaned_filename,
        content_type=content_type
    )
    new_filename, filepath = save_file(cleaned_file)
    cleaned_data_file = DataFile(
        filename=new_filename,
        file_type=file_extension,
        file_size=os.path.getsize(filepath),
        original_filename=data_file.filename,
        upload_date=datetime.now(),
        is_cleaned=True
    )
    db.session.add(cleaned_data_file)
    db.session.commit()

    report["cleaned_file_id"] = cleaned_data_file.id
    report["cleaned_filename"] = new_filename

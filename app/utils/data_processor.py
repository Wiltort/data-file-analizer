from datetime import datetime
from typing import Any, Dict
import pandas as pd
from flask import current_app
from sqlalchemy import select
from werkzeug.utils import secure_filename
import os
from app.extensions import db
from app.models import DataFile, DataAnalysis, DataPlot
from werkzeug.datastructures import FileStorage
from io import BytesIO
import tempfile
import matplotlib.pyplot as plt


reading_methods = {"csv": pd.read_csv, "xlsx": pd.read_excel}


def allowed_file(filename: str) -> bool:
    """
    Check if a filename has an allowed extension based on app configuration.
    
    Args:
        filename: Original filename to validate
        
    Returns:
        bool: True if extension is allowed, False otherwise
    """
    extensions = current_app.config["ALLOWED_EXTENSIONS"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in extensions


def save_file(file: FileStorage) -> tuple[str, str]:
    """
    Save uploaded file with unique filename to prevent overwrites.
    
    Generates sequential filenames if duplicate exists (e.g., "file (1).csv").
    
    Args:
        file: Werkzeug FileStorage object to save
        
    Returns:
        tuple: (unique_filename, full_filepath)
    """    
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


def analyze_data(file_id: int) -> dict:
    """
    Perform basic statistical analysis on a data file.
    
    Checks for existing analysis in database before computing new statistics.
    
    Args:
        file_id: ID of DataFile record to analyze
        
    Returns:
        dict: Statistical results including mean, median, correlation, etc.
        
    Raises:
        RuntimeError: If file processing fails
    """
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
    fill_missing: str = 'mean',
    force: bool = False,
) -> Dict[str, Any]:
    """
    Clean data by handling duplicates and missing values.
    
    Args:
        file_id: ID of DataFile record to clean
        handle_duplicates: 'drop' to remove or 'keep' to preserve duplicates
        fill_missing: Strategy for missing values ('mean', 'median', 'zero')
        force: Set True to force re-cleaning even if existing analysis exists
        
    Returns:
        dict: Cleaning report with metrics and new file information
        
    Raises:
        ValueError: For invalid cleaning parameters
        RuntimeError: If file processing fails
        
    Creates:
        - New DataFile entry for cleaned data
        - DataAnalysis record of cleaning operation
    """
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
    numeric_cols = df.select_dtypes(include=['number']).columns
    missing_before = df[numeric_cols].isnull().sum().to_dict()

    if fill_missing == 'mean':
        fill_values = df[numeric_cols].mean()
    elif fill_missing == 'median':
        fill_values = df[numeric_cols].median()
    elif fill_missing == 'zero':
        fill_values = 0
    else:
        raise ValueError("Invalid fill_missing. Valid: 'mean', 'median', 'zero'")
    
    df[numeric_cols] = df[numeric_cols].fillna(fill_values)
    missing_after = df[numeric_cols].isnull().sum().to_dict()

    data["missing_values_filled"] = sum(missing_before.values()) - sum(missing_after.values())
    data['cleaning_report']['missing_values_filled'] = {
        'before': missing_before,
        'after': missing_after,
        'method': fill_missing
    }
    data['cleaning_report']['actions_performed'].append('missing_values_filled')

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
    )
    db.session.add(cleaned_data_file)
    db.session.commit()
    data['cleaning_report']["cleaned_file_id"] = cleaned_data_file.id
    data['cleaning_report']["cleaned_filename"] = new_filename
    cleaning_analysis = DataAnalysis(
        data_file_id=file_id,
        analysis_date=datetime.now(),
        analysis_type=analysis_type,
        duplicates_removed=data["duplicates_removed"],
        missing_values_filled=data["missing_values_filled"],
        cleaning_report=data["cleaning_report"],
    )
    db.session.add(cleaning_analysis)
    db.session.commit()
    return data

def generate_plot(
        file_id: int,
        column: str,
        plot_type: str,
        x: str | None
):  
    stmt = select(DataPlot).where(
        DataPlot.data_file_id == file_id,
        DataPlot.plot_type == plot_type,
        DataPlot.columns_used.has_key(column))
    plot = db.session.scalar(stmt)
    if plot:
        img = BytesIO(plot.plot_data)
        img.seek(0)
        return img
    data_file = db.session.get(DataFile, file_id)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], data_file.filename)
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
    plt.figure()
    columns = [column]
    if plot_type == 'histogram':
        df[column].hist()
        plt.title(f'Histogram of {column}')
    elif plot_type == 'scatter':
        if x is None:
            x_col = df.columns[0]
        else:
            x_col = x
        columns.append(x_col)
        plt.scatter(df[x_col], df[column])
        plt.title(f'Scatter plot: {x_col} vs {column}')
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    img_data = img.getvalue()
    # Сохранение информации о графике в БД
    plot = DataPlot(
        data_file_id=file_id,
        plot_type=plot_type,
        plot_data=img_data,
        columns_used=df[columns].fillna(0).to_dict()
        # plot_json для фронта 
    )
    db.session.add(plot)
    db.session.commit()
    return img
import pandas as pd
from flask import current_app
from werkzeug.utils import secure_filename
import os


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

def analyze_data(file_path, analysis_type):
    pass

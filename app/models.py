from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, LargeBinary, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from .extensions import db, Base


class DataFile(Base):
    """
    Model for loaded files
    """
    __tablename__ = 'data_files'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # ['csv', 'xlsx', 'xls']
    upload_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    file_size: Mapped[int] = mapped_column(Integer)  # Размер файла в байтах
    original_filename: Mapped[str] = mapped_column(String(256))
    
    # Связь с анализом данных
    analyses: Mapped[list["DataAnalysis"]] = db.relationship(back_populates="data_file", lazy=True)
    
    def __repr__(self):
        return f'<DataFile {self.filename}>'
    

class DataAnalysis(Base):
    """
    Model for analyzes of datafiles
    """
    __tablename__ = 'data_analyses'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    data_file_id: Mapped[int] = mapped_column(ForeignKey('data_files.id'), nullable=False)
    analysis_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    analysis_type: Mapped[str | None] = mapped_column(String(50))  # 'basic_stats', 'cleaning', 'correlation' и т.д.
    
    # Статистические данные в JSON формате
    stats_mean: Mapped[dict | None] = mapped_column(JSONB)
    stats_median: Mapped[dict | None] = mapped_column(JSONB)
    stats_correlation: Mapped[dict | None] = mapped_column(JSONB)
    stats_std: Mapped[dict | None] = mapped_column(JSONB)
    stats_min: Mapped[dict | None] = mapped_column(JSONB)
    stats_max: Mapped[dict | None] = mapped_column(JSONB)
    
    # Информация об очистке данных
    duplicates_removed: Mapped[int | None] = mapped_column(Integer)
    missing_values_filled: Mapped[int | None] = mapped_column(Integer)
    cleaning_report: Mapped[dict | None] = mapped_column(JSONB)
    
    # Связи
    data_file: Mapped["DataFile"] = db.relationship(back_populates="analyses")
    plots: Mapped[list["DataPlot"]] = db.relationship(back_populates="data_analysis", lazy=True)
    
    def __repr__(self):
        return f'<DataAnalysis {self.analysis_type} for file {self.data_file_id}>'
    
    def get_stats(self):
        if self.analysis_type == 'basic_stats':
            stats = {
                'mean': self.stats_mean,
                'median': self.stats_median,
                'correllation': self.stats_correlation,
                'std': self.stats_std,
                'min': self.stats_min,
                'max': self.stats_max
            }
            return stats
        raise RuntimeError('Invalid analysis type')
            


class DataPlot(Base):
    """
    Модель для хранения сгенерированных графиков
    """
    __tablename__ = 'data_plots'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey('data_analyses.id'), nullable=False)
    plot_type: Mapped[str | None] = mapped_column(String(50))  # 'histogram', 'scatter', 'boxplot' и т.д.
    plot_data: Mapped[bytes | None] = mapped_column(LargeBinary)  # Бинарные данные изображения (для PNG)
    plot_json: Mapped[dict | None] = mapped_column(JSONB)  # Данные для построения графика на клиенте
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    columns_used: Mapped[dict | None] = mapped_column(JSONB)  # Колонки, использованные для построения графика
    
    # Связи
    data_analysis: Mapped["DataAnalysis"] = db.relationship(back_populates="plots")
    
    def __repr__(self):
        return f'<DataPlot {self.plot_type} for analysis {self.analysis_id}>'

class AnalysisTask(Base):
    """
    Модель для отслеживания асинхронных задач анализа
    """
    __tablename__ = 'analysis_tasks'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), unique=True)  # UUID задачи
    data_file_id: Mapped[int | None] = mapped_column(ForeignKey('data_files.id'))
    task_type: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default='PENDING')  # 'pending', 'processing', 'completed', 'failed'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    result: Mapped[dict | None] = mapped_column(JSONB)  # Результат выполнения задачи
    error: Mapped[str | None] = mapped_column(Text)  # Сообщение об ошибке, если есть
    
    def __repr__(self):
        return f'<AnalysisTask {self.task_id} ({self.status})>'
from datetime import datetime
from run import celery
from models import DataAnalysis, AnalysisTask, db
from utils.data_processor import analyze_data

@celery.task(bind=True)
def process_analysis(self, file_id, file_path, analysis_type):
    try:
        # Обновляем статус задачи
        task = AnalysisTask.query.filter_by(task_id=self.request.id).first()
        task.status = 'STARTED'
        db.session.commit()
        
        # Выполняем анализ
        result = analyze_data(file_path, analysis_type)
        
        # Сохраняем результат
        analysis = DataAnalysis(
            file_id=file_id,
            analysis_type=analysis_type,
            stats_mean=result.get('mean'),
            stats_median=result.get('median')
        )
        db.session.add(analysis)
        
        task.status = 'SUCCESS'
        task.result = result
        task.completed_at = datetime.now()
        db.session.commit()
        
        return result
    except Exception as e:
        task.status = 'FAILURE'
        task.error = str(e)
        db.session.commit()
        raise self.retry(exc=e, countdown=60, max_retries=3)
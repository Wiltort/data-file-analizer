def test_clean_data(client, sample_csv, db):
    """Тест запуска очистки данных"""
    upload_resp = client.post(
        '/api/v1/upload',
        data={'file': (sample_csv, 'clean_test.csv')},
        content_type='multipart/form-data'
    )
    file_id = upload_resp.json['id']
    
    clean_resp = client.post(f'/api/v1/data/{file_id}/clean')
    assert clean_resp.status_code == 202
    assert 'task_id' in clean_resp.json
    
    # Проверяем создание задачи в БД
    task = db.session.get(AnalysisTask, clean_resp.json['task_id'])
    assert task is not None
    assert task.file_id == file_id
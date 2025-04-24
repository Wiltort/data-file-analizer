from app.models import DataFile


def test_clean_data(client, sample_csv, db):
    """Тест запуска очистки данных"""
    with client.application.app_context():
        # Upload
        upload_resp = client.post(
            '/api/v1/upload',
            data={'file': (sample_csv, 'clean_test.csv')},
            content_type='multipart/form-data'
        )
        file_id = upload_resp.json['id']
        
        # Cleaning
        clean_resp = client.post(f'/api/v1/data/{file_id}/clean')
        
        # Assertions
        assert clean_resp.status_code == 202
        assert 'duplicates_removed' in clean_resp.json
        
        # Check cleaned file in DB
        cleaned_file = db.session.get(
            DataFile, 
            clean_resp.json['cleaning_report']['cleaned_file_id']
        )
        assert cleaned_file is not None
        second_clean_resp = client.post(f'/api/v1/data/{file_id}/clean',)
        assert clean_resp.json == second_clean_resp.json
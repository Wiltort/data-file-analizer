def test_generate_plot(client, sample_csv, db):
    """Тест генерации графика"""
    upload_resp = client.post(
        '/api/v1/upload',
        data={'file': (sample_csv, 'plot_test.csv')},
        content_type='multipart/form-data'
    )
    file_id = upload_resp.json['id']
    
    plot_resp = client.get(
        f'/api/v1/data/{file_id}/plot',
        query_string={'column': 'value', 'type': 'histogram'}
    )
    assert plot_resp.status_code == 200
    assert plot_resp.content_type == 'image/png'
    
    # Проверяем сохранение информации о графике в БД
    plot = DataPlot.query.filter_by(columns_used=['value']).first()
    assert plot is not None
    assert plot.plot_type == 'histogram'
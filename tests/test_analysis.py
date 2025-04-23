import pytest


def test_get_stats(client, sample_csv, db):
    """Тест получения статистики"""
    # Сначала загружаем файл
    upload_resp = client.post(
        "/api/v1/upload",
        data={"file": (sample_csv, "stats_test.csv")},
        content_type="multipart/form-data",
    )
    file_id = upload_resp.json["id"]

    # Запрашиваем статистику
    stats_resp = client.get(f"/api/v1/data/{file_id}/stats")
    assert stats_resp.status_code == 200
    data = stats_resp.json
    assert "mean" in data
    assert "value" in data["mean"]
    assert float(data["mean"]["value"]) == pytest.approx(15.5, 0.1)
    assert "median" in data
    assert "value" in data["median"]
    assert float(data["median"]["value"]) == pytest.approx(15.7, 0.1)

    # Повторный запрос должен сработать через сохраненный в базе анализ
    stats_resp_2 = client.get(f"/api/v1/data/{file_id}/stats")
    assert stats_resp_2.status_code == 200
    data_2 = stats_resp_2.json
    assert data == data_2


def test_stats_nonexistent_file(client):
    """Тест запроса статистики для несуществующего файла"""
    response = client.get("/api/v1/data/999/stats")
    assert response.status_code == 404

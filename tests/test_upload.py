from io import BytesIO


def test_upload_csv(client, sample_csv):
    """Тест загрузки CSV файла"""
    data = {"file": (sample_csv, "test.csv")}
    response = client.post(
        "/api/v1/upload", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 201
    assert "id" in response.json
    assert response.json["filename"] == "test.csv"


def test_upload_excel(client, sample_excel):
    """Тест загрузки Excel файла"""
    data = {"file": (sample_excel, "test.xlsx")}
    response = client.post(
        "/api/v1/upload", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 201
    assert response.json["filename"] == "test.xlsx"


def test_upload_invalid_type(client):
    """Тест загрузки файла неверного типа"""
    data = {"file": (BytesIO(b"test"), "test.txt")}
    response = client.post(
        "/api/v1/upload", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 415

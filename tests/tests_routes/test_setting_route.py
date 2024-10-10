import pytest
from unittest.mock import patch, Mock
from run import app as real_app


@pytest.fixture
def client():
    real_app.config['TESTING'] = True
    with real_app.test_client() as client:
        yield client


@pytest.fixture
def mock_db():
    with patch('src.routes.setting_route.coll_settings') as mock_db:
        yield mock_db


def test_add_setting(client, mock_db):
    mock_db.insert_one.return_value = Mock(inserted_id="12345")
    setting_data = {"name": "TestSetting", "values": ["value1", "value2"]}
    response = client.post('/setting', json=setting_data)
    assert response.status_code == 201
    assert response.json['msg'] == "El/la configuración con id '12345' ha sido añadido/a de forma satisfactoria"


def test_get_settings(client, mock_db):
    mock_db.find.return_value = [{"name": "TestSetting", "values": ["value1", "value2"]}]
    response = client.get('/settings')
    assert response.status_code == 200
    assert response.get_json()[0]['name'] == "TestSetting"
    assert response.get_json()[0]['values'] == ["value1", "value2"]


def test_get_setting(client, mock_db):
    mock_db.find_one.return_value = {"name": "TestSetting", "values": ["value1", "value2"]}
    response = client.get('/setting/12345')
    assert response.status_code == 200
    assert response.json['name'] == "TestSetting"
    assert response.json['values'] == ["value1", "value2"]


def test_update_setting(client, mock_db):
    mock_db.find_one.return_value = {"name": "TestSetting", "values": ["value1", "value2"]}
    mock_db.find_one_and_update.return_value = {"name": "UpdatedSetting", "values": ["value1", "value2"]}
    setting_data = {"name": "UpdatedSetting"}
    response = client.put('/setting/12345', json=setting_data)
    assert response.status_code == 200
    assert response.json['name'] == "UpdatedSetting"
    assert response.json['values'] == ["value1", "value2"]


def test_delete_setting(client, mock_db):
    mock_db.delete_one.return_value = Mock(deleted_count=1)
    response = client.delete('/setting/12345')
    assert response.status_code == 200
    assert response.json['msg'] == "El/la configuración con id '12345' ha sido eliminado/a de forma satisfactoria"

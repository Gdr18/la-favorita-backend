import pytest
from unittest.mock import MagicMock
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from src import app as real_app


@pytest.fixture
def app():
    real_app.config['TESTING'] = True
    yield real_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_db(mocker):
    mock_db = MagicMock()
    mocker.patch('src.routes.setting_route.coll_settings', new=mock_db)
    return mock_db


def test_add_setting(client, mock_db):
    mock_db.insert_one.return_value.inserted_id = ObjectId()
    response = client.post('/setting', json={'name': 'test', 'values': ['value1', 'value2']})
    assert response.status_code == 201
    assert 'id' in response.json['msg']


def test_add_setting_duplicate_key(client, mock_db):
    mock_db.insert_one.side_effect = DuplicateKeyError("Duplicate key error")
    response = client.post('/setting', json={'name': 'test', 'values': ['value1', 'value2']})
    assert response.status_code == 409


def test_get_settings(client, mock_db):
    mock_db.find.return_value = [{'key': 'value'}]
    response = client.get('/settings')
    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_get_setting(client, mock_db):
    mock_db.find_one.return_value = {'_id': ObjectId(), 'key': 'value'}
    response = client.get('/setting/507f1f77bcf86cd799439011')
    assert response.status_code == 200
    assert 'key' in response.json


def test_get_setting_not_found(client, mock_db):
    mock_db.find_one.return_value = None
    response = client.get('/setting/507f1f77bcf86cd799439011')
    assert response.status_code == 404


def test_update_setting(client, mock_db):
    mock_db.find_one.return_value = {'name': 'value', 'values': ['value1', 'value2']}
    mock_db.find_one_and_update.return_value = {'name': 'new_value'}
    response = client.put('/setting/507f1f77bcf86cd799439011', json={'name': 'new_value'})
    assert response.status_code == 200
    assert 'name' in response.json


def test_delete_setting(client, mock_db):
    mock_db.delete_one.return_value.deleted_count = 1
    response = client.delete('/setting/507f1f77bcf86cd799439011')
    assert response.status_code == 200
    assert 'id' in response.json['msg']


def test_delete_setting_not_found(client, mock_db):
    mock_db.delete_one.return_value.deleted_count = 0
    response = client.delete('/setting/507f1f77bcf86cd799439011')
    assert response.status_code == 404


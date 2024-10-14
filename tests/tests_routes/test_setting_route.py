import pytest
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from pydantic import ValidationError

from src import app as real_app
from src.utils.exceptions_management import ResourceNotFoundError


URL_SETTING = '/setting'
URL_SETTINGS = '/settings'
URL_SETTING_ID = '/setting/507f1f77bcf86cd799439011'


@pytest.fixture
def app():
    real_app.config['TESTING'] = True
    yield real_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_db(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch('src.routes.setting_route.coll_settings', new=mock_db)
    return mock_db


@pytest.fixture
def valid_setting_data():
    return {'name': 'test', 'values': ['value1', 'value2']}


@pytest.fixture
def invalid_setting_data():
    return {'name': 12345, 'values': ['value1', 'value2']}


def test_add_setting(client, mock_db, valid_setting_data):
    mock_db.insert_one.return_value.inserted_id = ObjectId()
    response = client.post(URL_SETTING, json=valid_setting_data)
    assert response.status_code == 201
    assert 'id' in response.json['msg']


def test_add_setting_duplicate_key(client, mock_db, mocker, valid_setting_data):
    error = DuplicateKeyError("E11000 duplicate key error")
    mocker.patch('pymongo.errors.DuplicateKeyError.details', new_callable=mocker.PropertyMock, return_value={"keyValue": {"name": "test"}})
    mock_db.insert_one.side_effect = error
    response = client.post(URL_SETTING, json=valid_setting_data)
    assert response.status_code == 409
    assert 'err' in response.json


def test_add_setting_validation_error(client, mock_db, mocker, invalid_setting_data):
    error = mocker.Mock(spec=ValidationError)
    mock_db.insert_one.side_effect = error
    response = client.post(URL_SETTING, json=invalid_setting_data)
    assert response.status_code == 400
    assert 'err' in response.json


def test_add_setting_unexpected_error(client, mock_db, mocker):
    mocker.patch('src.routes.setting_route.coll_settings.insert_one', side_effect=Exception("Unexpected Error"))
    response = client.post(URL_SETTING)
    assert response.status_code == 500
    assert 'err' in response.json


def test_get_settings(client, mock_db):
    mock_db.find.return_value = [{'key': 'value'}]
    response = client.get(URL_SETTINGS)
    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_get_settings_unexpected_error(client, mock_db, mocker):
    mocker.patch('src.routes.setting_route.coll_settings.find', side_effect=Exception("Unexpected Error"))
    response = client.get(URL_SETTINGS)
    assert response.status_code == 500


def test_get_setting(client, mock_db):
    mock_db.find_one.return_value = {'_id': ObjectId(), 'key': 'value'}
    response = client.get(URL_SETTING_ID)
    assert response.status_code == 200
    assert 'key' in response.json


def test_get_setting_not_found(app, client, mock_db):
    with real_app.app_context():
        mock_db.find_one.return_value = None
        response = client.get(URL_SETTING_ID)
        assert response.status_code == 404
        assert response.json['err'] == "El/la configuración con id '507f1f77bcf86cd799439011' no ha sido encontrado/a."

        error = ResourceNotFoundError('507f1f77bcf86cd799439011', 'setting')
        mock_db.find_one.side_effect = error
        response = client.get(URL_SETTING_ID)
        assert response.status_code == 404
        assert response.json['err'] == "El/la setting con id '507f1f77bcf86cd799439011' no ha sido encontrado/a."


def test_get_setting_unexpected_error(client, mock_db, mocker):
    mocker.patch('src.routes.setting_route.coll_settings.find_one', side_effect=Exception("Unexpected Error"))
    response = client.get(URL_SETTING_ID)
    assert response.status_code == 500


def test_update_setting(client, mock_db):
    mock_db.find_one.return_value = {'name': 'value', 'values': ['value1', 'value2']}
    mock_db.find_one_and_update.return_value = {'name': 'new_value'}
    response = client.put(URL_SETTING_ID, json={'name': 'new_value'})
    assert response.status_code == 200
    assert 'name' in response.json


def test_update_setting_not_found(client, mock_db):
    with real_app.app_context():
        mock_db.find_one.return_value = None
        response = client.put(URL_SETTING_ID)
        assert response.status_code == 404
        assert response.json['err'] == "El/la configuración con id '507f1f77bcf86cd799439011' no ha sido encontrado/a."

        error = ResourceNotFoundError('507f1f77bcf86cd799439011', 'setting')
        mock_db.find_one.side_effect = error
        response = client.put(URL_SETTING_ID)
        assert response.status_code == 404
        assert response.json['err'] == "El/la setting con id '507f1f77bcf86cd799439011' no ha sido encontrado/a."


def test_update_setting_duplicate_key(client, mock_db, mocker):
    error = DuplicateKeyError("E11000 duplicate key error")
    mocker.patch('pymongo.errors.DuplicateKeyError.details', new_callable=mocker.PropertyMock, return_value={"keyValue": {"name": "new_value"}})
    mock_db.find_one.return_value = {'name': 'value', 'values': ['value1', 'value2']}
    mock_db.find_one_and_update.side_effect = error
    response = client.put(URL_SETTING_ID, json={'name': 'new_value'})
    assert response.status_code == 409
    assert response.json['err'] == "Error de clave duplicada en MongoDB: {'name': 'new_value'}"


def test_update_setting_validation_error(client, mock_db, mocker, invalid_setting_data):
    error = mocker.Mock(spec=ValidationError)
    mock_db.insert_one.side_effect = error
    response = client.put(URL_SETTING_ID, json=invalid_setting_data)
    assert response.status_code == 400
    assert 'err' in response.json


def test_update_setting_unexpected_error(client, mock_db, mocker):
    mocker.patch('src.routes.setting_route.coll_settings.find_one_and_update', side_effect=Exception("Unexpected Error"))
    response = client.put(URL_SETTING_ID)
    assert response.status_code == 500


def test_delete_setting(client, mock_db):
    mock_db.delete_one.return_value.deleted_count = 1
    response = client.delete(URL_SETTING_ID)
    assert response.status_code == 200
    assert 'id' in response.json['msg']


def test_delete_setting_not_found(app, client, mock_db):
    with real_app.app_context():
        mock_db.delete_one.return_value.deleted_count = 0
        response = client.delete(URL_SETTING_ID)
        assert response.status_code == 404
        assert response.json['err'] == "El/la configuración con id '507f1f77bcf86cd799439011' no ha sido encontrado/a."

        error = ResourceNotFoundError('507f1f77bcf86cd799439011', 'setting')
        mock_db.delete_one.side_effect = error
        response = client.delete(URL_SETTING_ID)
        assert response.status_code == 404
        assert response.json['err'] == "El/la setting con id '507f1f77bcf86cd799439011' no ha sido encontrado/a."


def test_delete_setting_unexpected_error(client, mock_db, mocker):
    mocker.patch('src.routes.setting_route.coll_settings.delete_one', side_effect=Exception("Unexpected Error"))
    response = client.delete(URL_SETTING_ID)
    assert response.status_code == 500

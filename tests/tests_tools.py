from typing import Union
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from pydantic import ValidationError

from src.utils.exceptions_management import ResourceNotFoundError


def validate_error_response(function: tuple, expected_status_code: int, expected_error_message: Union[str, list[str]]):
    response, status_code = function
    assert status_code == expected_status_code
    assert response.get_json()['err'] == expected_error_message


def validate_success_response(function: tuple, expected_status_code: int, expected_success_message: str):
    response, status_code = function
    assert status_code == expected_status_code
    assert response.get_json()['msg'] == expected_success_message


# Funciones reutilizables para los tests de las rutas
def request_adding_valid_resource(client, mock_db, url_resource: str, valid_resource_data: dict):
    mock_db.insert_one.return_value.inserted_id = ObjectId()
    response = client.post(url_resource, json=valid_resource_data)
    assert response.status_code == 201
    assert 'id' in response.json['msg']


def request_getting_resources(client, mock_db, url_resource: str, valid_resource_data: dict):
    mock_db.find.return_value = [valid_resource_data]
    response = client.get(url_resource)
    assert response.status_code == 200
    assert isinstance(response.json, list)


def request_getting_resource(client, mock_db, url_resource: str, valid_resource_data: dict):
    mock_db.find_one.return_value = {'_id': ObjectId(), **valid_resource_data}
    response = client.get(url_resource)
    assert response.status_code == 200
    assert isinstance(response.json, dict)


def request_updating_resource(client, mock_db, url_resource: str, valid_resource_data: dict, updated_resource_data: dict):
    mock_db.find_one.return_value = valid_resource_data
    mock_db.find_one_and_update.return_value = {**valid_resource_data, **updated_resource_data}
    response = client.put(url_resource, json=updated_resource_data)
    assert response.status_code == 200
    assert isinstance(response.json, dict)


def request_deleting_resource(client, mock_db, url_resource: str):
    mock_db.delete_one.return_value.deleted_count = 1
    response = client.delete(url_resource)
    assert response.status_code == 200
    assert 'id' in response.json['msg']


def request_resource_not_found(app, client, mock_db, method: str, url_resource: str):
    with app.app_context():
        response = None
        if method == 'delete':
            mock_db.delete_one.return_value.deleted_count = 0
            response = client.delete(url_resource)
        else:
            mock_db.find_one.return_value = None
            if method == 'get':
                response = client.get(url_resource)
            if method == 'put':
                response = client.put(url_resource)
        assert response.status_code == 404
        assert 'err' in response.json


def request_resource_not_found_error(client, mock_db, method: str, url_resource: str, valid_resource_data: dict, resource: str):
    error = ResourceNotFoundError(valid_resource_data.get('_id'), resource)
    response = None
    if method == 'delete':
        mock_db.delete_one.side_effect = error
        response = client.delete(url_resource)
    else:
        mock_db.find_one.side_effect = error
        if method == 'get':
            response = client.get(url_resource)
        elif method == 'put':
            response = client.put(url_resource)
    assert response.status_code == 404
    assert 'err' in response.json


def request_invalid_resource_duplicate_key_error(client, mock_db, mocker, method: str, url_resource: str, valid_resource_data: dict, updated_resource_data, field_required: str = None):
    error = DuplicateKeyError("E11000 duplicate key error")
    mocker.patch('pymongo.errors.DuplicateKeyError.details', new_callable=mocker.PropertyMock, return_value={"keyValue": updated_resource_data if method == 'put' else {field_required: valid_resource_data.get(field_required)}})
    response = None
    if method == 'post':
        mock_db.insert_one.side_effect = error
        response = client.post(url_resource, json=valid_resource_data)
    elif method == 'put':
        mock_db.find_one.return_value = valid_resource_data
        mock_db.find_one_and_update.side_effect = error
        response = client.put(url_resource, json=updated_resource_data)
    assert response.status_code == 409
    assert 'err' in response.json


def request_invalid_resource_validation_error(client, mock_db, mocker, method: str, url_resource: str, invalid_resource_data: dict):
    error = mocker.Mock(spec=ValidationError)
    response = None
    if method == 'post':
        mock_db.insert_one.side_effect = error
        response = client.post(url_resource, json=invalid_resource_data)
    elif method == 'put':
        mock_db.update_one.side_effect = error
        response = client.put(url_resource, json=invalid_resource_data)
    assert response.status_code == 400
    assert 'err' in response.json


def request_unexpected_error(client, mocker, request: str, url_resource: str):
    mocker.patch(f'src.routes.setting_route.coll_settings.{request}', side_effect=Exception("Unexpected Error"))
    response = None
    if any([request == 'find', request == 'find_one']):
        response = client.get(url_resource)
    elif request == 'insert_one':
        response = client.post(url_resource)
    elif request == 'find_one_and_update':
        response = client.put(url_resource)
    elif request == 'delete_one':
        response = client.delete(url_resource)
    assert response.status_code == 500
    assert 'err' in response.json


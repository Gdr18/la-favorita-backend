from typing import Union
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from pydantic import ValidationError

from src.utils.exceptions_management import ClientCustomError


def validate_error_response(function: tuple, expected_status_code: int, expected_error_message: Union[str, list[str]]):
    response, status_code = function
    assert status_code == expected_status_code
    assert response.json['err'] == expected_error_message


def validate_success_response(function: tuple, expected_status_code: int, expected_success_message: str):
    response, status_code = function
    assert status_code == expected_status_code
    assert response.json['msg'] == expected_success_message


# Funciones reutilizables para los tests de las rutas
def request_adding_valid_resource(client, mock_db, header, url_resource: str, valid_resource_data: dict):
    mock_db.insert_one.return_value.inserted_id = ObjectId()
    response = client.post(url_resource, json=valid_resource_data, headers=header)
    assert response.status_code == 201
    assert 'msg' in response.json


def request_getting_resources(client, mock_db, header, url_resource: str, valid_resource_data: dict):
    mock_db.find.return_value = [valid_resource_data]
    response = client.get(url_resource, headers=header)
    assert response.status_code == 200
    assert isinstance(response.json, list)


def request_getting_resource(client, mock_db, header, url_resource: str, valid_resource_data: dict):
    mock_db.find_one.return_value = valid_resource_data
    response = client.get(url_resource, headers=header)
    assert response.status_code == 200
    assert isinstance(response.json, dict)


def request_updating_resource(client, mock_db, header, url_resource: str, valid_resource_data: dict, updated_resource_data: dict):
    mock_db.find_one.return_value = valid_resource_data
    mock_db.find_one_and_update.return_value = {**valid_resource_data, **updated_resource_data}
    response = client.put(url_resource, json=updated_resource_data, headers=header)
    assert response.status_code == 200
    assert isinstance(response.json, dict)


def request_deleting_resource(client, mock_db, header, url_resource: str):
    mock_db.delete_one.return_value.deleted_count = 1
    response = client.delete(url_resource, headers=header)
    assert response.status_code == 200
    assert 'msg' in response.json


def request_unauthorized_access(client, header, mock_jwt, request, url_resource: str, valid_resource_data: dict):
    response = None
    mock_jwt.return_value = {'role': 3}
    if request == 'post':
        response = client.post(url_resource, json=valid_resource_data, headers=header)
    elif request == 'get':
        response = client.get(url_resource, headers=header)
    elif request == 'put':
        response = client.put(url_resource, json=valid_resource_data, headers=header)
    elif request == 'delete':
        response = client.delete(url_resource, headers=header)
    assert response.status_code == 401
    assert 'err' in response.json


def request_resource_not_found(app, client, mock_db, header, method: str, url_resource: str):
    with app.app_context():
        response = None
        if method == 'delete':
            mock_db.delete_one.return_value.deleted_count = 0
            response = client.delete(url_resource, headers=header)
        else:
            mock_db.find_one.return_value = None
            if method == 'get':
                response = client.get(url_resource, headers=header)
            if method == 'put':
                response = client.put(url_resource, headers=header)
        assert response.status_code == 404
        assert 'err' in response.json


def request_resource_not_found_error(client, mock_db, header, method: str, url_resource: str, valid_resource_data: dict, resource: str):
    error = ClientCustomError(resource, "not_found")
    response = None
    if method == 'delete':
        mock_db.delete_one.side_effect = error
        response = client.delete(url_resource, headers=header)
    else:
        mock_db.find_one.side_effect = error
        if method == 'get':
            response = client.get(url_resource, headers=header)
        elif method == 'put':
            response = client.put(url_resource, headers=header)
    assert response.status_code == 404
    assert 'err' in response.json


def request_invalid_resource_duplicate_key_error(client, mock_db, header, mocker, method: str, url_resource: str, valid_resource_data: dict, updated_resource_data, field_required: str = None):
    error = DuplicateKeyError("E11000 duplicate key error")
    mocker.patch('pymongo.errors.DuplicateKeyError.details', new_callable=mocker.PropertyMock, return_value={"keyValue": updated_resource_data if method == 'put' else {field_required: valid_resource_data.get(field_required)}})
    response = None
    if method == 'post':
        mock_db.insert_one.side_effect = error
        response = client.post(url_resource, json=valid_resource_data, headers=header)
    elif method == 'put':
        mock_db.find_one.return_value = valid_resource_data
        mock_db.find_one_and_update.side_effect = error
        response = client.put(url_resource, json=updated_resource_data, headers=header)
    assert response.status_code == 409
    assert 'err' in response.json


def request_invalid_resource_validation_error(client, mock_db, header, method: str, url_resource: str, invalid_resource_data: dict):
    response = None
    if method == 'post':
        mock_db.insert_one.side_effect = ValidationError
        response = client.post(url_resource, json=invalid_resource_data, headers=header)
    elif method == 'put':
        mock_db.update_one.side_effect = ValidationError
        response = client.put(url_resource, json=invalid_resource_data, headers=header)
    assert response.status_code == 400
    assert 'err' in response.json


def request_unexpected_error(client, mock_db, header, request: str, url_resource: str):
    response = None
    if request == 'find':
        mock_db.find.side_effect = Exception("Unexpected Error")
        response = client.get(url_resource, headers=header)
    elif request == 'find_one':
        mock_db.find_one.side_effect = Exception("Unexpected Error")
        response = client.get(url_resource, headers=header)
    elif request == 'insert_one':
        mock_db.insert_one.side_effect = Exception("Unexpected Error")
        response = client.post(url_resource, headers=header)
    elif request == 'find_one_and_update':
        mock_db.find_one_and_update.side_effect = Exception("Unexpected Error")
        response = client.put(url_resource, headers=header)
    elif request == 'delete_one':
        mock_db.delete_one.side_effect = Exception("Unexpected Error")
        response = client.delete(url_resource, headers=header)

    assert response.status_code == 500
    assert 'err' in response.json

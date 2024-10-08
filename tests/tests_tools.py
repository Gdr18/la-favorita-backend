def validate_error_response(function: tuple, expected_status_code: int, expected_error_message: str or list):
    response, status_code = function
    assert status_code == expected_status_code
    assert response.get_json()['err'] == expected_error_message


def validate_success_response(function: tuple, expected_status_code: int, expected_success_message: str):
    response, status_code = function
    assert status_code == expected_status_code
    assert response.get_json()['msg'] == expected_success_message

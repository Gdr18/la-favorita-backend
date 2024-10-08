def validate_error_response(function, expected_status_code, expected_error_message):
    response, status_code = function()
    assert status_code == expected_status_code
    assert response.get_json()['err'] == expected_error_message


def validate_success_response(function, expected_status_code, expected_success_message):
    response, status_code = function
    assert status_code == expected_status_code
    assert response.get_json()['msg'] == expected_success_message

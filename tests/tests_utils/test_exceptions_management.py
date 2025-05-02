import pytest
from pydantic import ValidationError

from run import app as real_app
from src.models.product_model import ProductModel
from src.models.user_model import UserModel
from src.utils.exception_handlers import ValueCustomError
from tests.test_helpers import validate_error_response_specific

code_validation_error = 400


@pytest.fixture
def app():
    real_app.testing = True
    return real_app

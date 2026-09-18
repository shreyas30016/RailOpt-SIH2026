import pytest
import base64
import json
from starlette.testclient import TestClient

DEFAULT_CONTROLLER_PAYLOAD = {
    "username": "default_test_controller",
    "role": "CONTROLLER",
    "division_code": "NDL",
    "division_name": "Northern Railway — Delhi Division",
    "can_approve": True,
    "can_optimize": True,
    "can_edit": True,
    "initial": "C",
    "corridor": "NDLS - AGC Semi-High Speed"
}
DEFAULT_TOKEN = base64.b64encode(json.dumps(DEFAULT_CONTROLLER_PAYLOAD).encode()).decode()

_orig_request = TestClient.request

def _patched_request(self, method, url, *args, **kwargs):
    headers = kwargs.get("headers")
    if headers is None:
        kwargs["headers"] = {"Authorization": f"Bearer {DEFAULT_TOKEN}"}
    elif isinstance(headers, dict):
        if "Authorization" not in headers and "X-Anonymous" not in headers:
            kwargs["headers"] = {**headers, "Authorization": f"Bearer {DEFAULT_TOKEN}"}
        elif headers.get("Authorization") is None:
            new_headers = {k: v for k, v in headers.items() if k != "Authorization"}
            kwargs["headers"] = new_headers
    return _orig_request(self, method, url, *args, **kwargs)

@pytest.fixture(autouse=True, scope="session")
def auto_auth_testclient():
    TestClient.request = _patched_request
    yield
    TestClient.request = _orig_request

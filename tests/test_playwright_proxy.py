from veri_py.core.playwright_proxy import playwright_proxy_from_url


def test_playwright_proxy_http_no_auth() -> None:
    assert playwright_proxy_from_url("http://proxy.example.com:8888") == {
        "server": "http://proxy.example.com:8888",
    }


def test_playwright_proxy_https_with_credentials() -> None:
    assert playwright_proxy_from_url("http://user:p%40ss@proxy.example.com:8888") == {
        "server": "http://proxy.example.com:8888",
        "username": "user",
        "password": "p@ss",
    }

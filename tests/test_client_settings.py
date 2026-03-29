from veri_py import AsyncVerifierClient, DirectServiceProxyMode, VerifierClient, VerifierSettings


def test_client_proxy_override_merges_into_settings() -> None:
    base = VerifierSettings()
    client = AsyncVerifierClient(base, proxy="http://127.0.0.1:9")
    assert client.settings.network_proxy_url == "http://127.0.0.1:9"

    sync = VerifierClient(base, proxy="http://127.0.0.1:8", direct_service_proxy_mode=DirectServiceProxyMode.RETRY_WITH_PROXY)
    assert sync.settings.network_proxy_url == "http://127.0.0.1:8"
    assert sync.settings.direct_service_proxy_mode == DirectServiceProxyMode.RETRY_WITH_PROXY

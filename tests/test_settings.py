from veri_py.core.config import DirectServiceProxyMode, VerifierSettings


def test_direct_service_proxy_mode_from_env() -> None:
    settings = VerifierSettings(VERI_DIRECT_SERVICE_PROXY_MODE="retry_with_proxy")
    assert settings.direct_service_proxy_mode == DirectServiceProxyMode.RETRY_WITH_PROXY

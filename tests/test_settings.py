from veri_py.core.config import VerifierSettings


def test_fallback_proxy_urls_parsing() -> None:
    settings = VerifierSettings(FALLBACK_PROXIES=" https://a.example/verify?reference= , https://b.example/verify?reference= ")
    assert settings.fallback_proxy_urls == [
        "https://a.example/verify?reference=",
        "https://b.example/verify?reference=",
    ]

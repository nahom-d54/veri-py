"""Map proxy URLs to Playwright proxy configuration."""

from __future__ import annotations

from urllib.parse import unquote, urlparse


def playwright_proxy_from_url(url: str) -> dict[str, str]:
    """Convert http(s)/socks URL into Playwright's ``proxy`` dict."""
    parsed = urlparse(url)
    netloc = parsed.netloc
    if "@" in netloc:
        userinfo, _, hostport = netloc.rpartition("@")
        server = f"{parsed.scheme}://{hostport}"
        if ":" in userinfo:
            username, _, password = userinfo.partition(":")
            return {
                "server": server,
                "username": unquote(username),
                "password": unquote(password),
            }
        return {"server": server, "username": unquote(userinfo)}
    return {"server": f"{parsed.scheme}://{netloc}"}

import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeURL(ValueError):
    pass


def validate_external_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafeURL("only HTTP(S) URLs with a hostname are allowed")
    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"}:
        raise UnsafeURL("localhost is not an external source")
    try:
        addresses = {ipaddress.ip_address(item[4][0]) for item in socket.getaddrinfo(host, None)}
    except socket.gaierror as exc:
        raise UnsafeURL("hostname could not be resolved") from exc
    if any(
        address.is_private or address.is_loopback or address.is_link_local or address.is_reserved
        for address in addresses
    ):
        raise UnsafeURL("private or reserved network targets are not allowed")
    return parsed._replace(fragment="").geturl()


def looks_blocked(text: str, status_code: int | None = None) -> bool:
    markers = (
        "captcha",
        "cloudflare",
        "turnstile",
        "recaptcha",
        "hcaptcha",
        "verify you are human",
        "access denied",
    )
    return status_code in {403, 429, 503} or any(marker in text.lower() for marker in markers)

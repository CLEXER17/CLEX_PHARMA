import httpx

from app.ingestion.security import looks_blocked, validate_external_url


class SourceBlocked(RuntimeError):
    pass


class SafeHTTPClient:
    def __init__(self, timeout: float = 20.0, max_bytes: int = 5_000_000):
        self.timeout = timeout
        self.max_bytes = max_bytes

    async def get_text(self, url: str) -> str:
        safe_url = validate_external_url(url)
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            max_redirects=5,
            headers={"User-Agent": "CLEX-Pharma/0.1 (+career research bot)"},
        ) as client:
            async with client.stream("GET", safe_url) as response:
                if response.status_code in {403, 429, 503}:
                    raise SourceBlocked(f"ACCESS_BLOCKED_CAPTCHA: HTTP {response.status_code}")
                chunks, size = [], 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > self.max_bytes:
                        raise ValueError("source response exceeds configured size limit")
                    chunks.append(chunk)
                body = b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")
        if looks_blocked(body):
            raise SourceBlocked("ACCESS_BLOCKED_CAPTCHA: challenge page detected")
        return body

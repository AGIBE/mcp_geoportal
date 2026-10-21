import asyncio
from dataclasses import dataclass

import httpx2


@dataclass
class APICheckResult:
    name: str
    url: str
    ok: bool
    error: str | None = None


async def _check_single_api(
    client: httpx2.AsyncClient, name: str, url: str
) -> APICheckResult:
    try:
        response = await client.head(url)
        response.raise_for_status()
        return APICheckResult(name=name, url=url, ok=True)
    except httpx2.TimeoutException:
        return APICheckResult(name=name, url=url, ok=False, error="Timeout")
    except httpx2.HTTPStatusError as e:
        return APICheckResult(
            name=name, url=url, ok=False, error=f"Status {e.response.status_code}"
        )
    except httpx2.RequestError as e:
        return APICheckResult(name=name, url=url, ok=False, error=str(e))


async def check_external_apis(readyness_urls: dict[str, str]) -> list[APICheckResult]:
    """Prüft alle konfigurierten externen APIs parallel."""
    async with httpx2.AsyncClient(timeout=3.0) as client:
        results = await asyncio.gather(
            *[
                _check_single_api(client, name, url)
                for name, url in readyness_urls.items()
            ]
        )
    return list(results)

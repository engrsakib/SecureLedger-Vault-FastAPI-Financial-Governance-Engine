from fastapi import Request

from app.core.url import get_public_base_url


def auth_links(request: Request) -> dict[str, str]:
    base = get_public_base_url(request)
    return {
        "login": f"{base}/auth/login",
        "register": f"{base}/auth/register",
        "refresh": f"{base}/auth/refresh",
        "logout": f"{base}/auth/logout",
    }


def transaction_links(request: Request, transaction_id: int | None = None) -> dict[str, str]:
    base = get_public_base_url(request)
    links = {
        "list": f"{base}/transactions",
        "create": f"{base}/transactions",
        "filter": f"{base}/transactions/filter",
    }
    if transaction_id is not None:
        links["self"] = f"{base}/transactions/{transaction_id}"
    return links
